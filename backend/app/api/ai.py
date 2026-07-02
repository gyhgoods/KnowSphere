import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.ai_schemas import (
    AskRequest,
    AskResponse,
    CitationRead,
    ConversationRead,
    FeedbackRead,
    FeedbackRequest,
    MessageRead,
)
from app.api.dependencies import DB, CurrentUser
from app.common.exceptions import AppError
from app.knowledge_models import (
    AIConversation,
    AIFeedback,
    AIMessage,
    ConversationStatus,
    MessageRole,
)
from app.services.rag import (
    RAGContext,
    RAGProviderError,
    coalesce_contexts,
    get_rag_provider,
    retrieve_contexts,
)
from app.services.storage import get_storage

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def conversation_read(conversation: AIConversation) -> ConversationRead:
    return ConversationRead(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def message_read(message: AIMessage) -> MessageRead:
    return MessageRead(
        id=message.id,
        role=message.role,
        content=message.content,
        citations=message.citations,
        confidence=message.confidence,
        model_name=message.model_name,
        created_at=message.created_at,
    )


async def unique_citations(contexts: list[RAGContext]) -> list[dict[str, object]]:
    citations: list[dict[str, object]] = []
    seen_sources: set[tuple[int, str]] = set()
    for context in contexts:
        source_key = (
            context.document_id,
            context.image_object_name or context.source_name,
        )
        if source_key in seen_sources:
            continue
        seen_sources.add(source_key)
        image_url = None
        if context.image_object_name:
            image_url = await run_in_threadpool(
                get_storage().presigned_get,
                context.image_object_name,
                900,
            )
        citations.append(
            CitationRead(
                index=len(citations) + 1,
                document_id=context.document_id,
                document_title=context.document_title,
                chunk_id=context.chunk_id,
                source_name=context.source_name,
                excerpt=context.content[:500],
                score=context.score,
                source_type=context.source_type,
                image_url=image_url,
                image_name=context.image_name,
                image_mime_type=context.image_mime_type,
                image_document_title=context.image_document_title,
            ).model_dump()
        )
    return citations


def json_event(event: str, data: dict[str, object]) -> str:
    return json.dumps({"event": event, "data": data}, ensure_ascii=False) + "\n"


async def get_user_conversation(
    db: DB, user: CurrentUser, conversation_id: int
) -> AIConversation:
    conversation = await db.scalar(
        select(AIConversation).where(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user.id,
        )
    )
    if not conversation:
        raise AppError("conversation_not_found", "Conversation does not exist", 404)
    return conversation


async def prepare_conversation(
    payload: AskRequest, db: DB, user: CurrentUser
) -> tuple[AIConversation, list[RAGContext], list[dict[str, object]]]:
    if payload.conversation_id:
        conversation = await get_user_conversation(db, user, payload.conversation_id)
    else:
        conversation = AIConversation(
            title=payload.question[:80],
            user_id=user.id,
            status=ConversationStatus.ACTIVE,
        )
        db.add(conversation)
        await db.flush()

    contexts = coalesce_contexts(
        await retrieve_contexts(
            db,
            user,
            payload.question,
            space_id=payload.space_id,
            limit=payload.limit,
        )
    )
    citations = await unique_citations(contexts)
    return conversation, contexts, citations


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(db: DB, user: CurrentUser) -> list[ConversationRead]:
    rows = (
        await db.execute(
            select(AIConversation)
            .where(
                AIConversation.user_id == user.id,
                AIConversation.status == ConversationStatus.ACTIVE,
            )
            .order_by(AIConversation.updated_at.desc())
        )
    ).scalars()
    return [conversation_read(row) for row in rows]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: int, db: DB, user: CurrentUser
) -> list[MessageRead]:
    await get_user_conversation(db, user, conversation_id)
    rows = (
        await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at, AIMessage.id)
        )
    ).scalars()
    return [message_read(row) for row in rows]


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, db: DB, user: CurrentUser) -> AskResponse:
    conversation, contexts, citations = await prepare_conversation(payload, db, user)
    try:
        provider = get_rag_provider()
        answer = await run_in_threadpool(provider.answer, payload.question, contexts)
    except RAGProviderError as exc:
        raise AppError("rag_provider_unavailable", str(exc), 503) from exc

    question_message = AIMessage(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=payload.question,
        citations=[],
        confidence=None,
        model_name=None,
    )
    answer_message = AIMessage(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=answer.answer,
        citations=citations,
        confidence=answer.confidence,
        model_name=answer.model,
    )
    db.add_all([question_message, answer_message])
    await db.commit()
    await db.refresh(question_message)
    await db.refresh(answer_message)
    return AskResponse(
        conversation_id=conversation.id,
        question_message_id=question_message.id,
        answer_message_id=answer_message.id,
        answer=answer.answer,
        confidence=answer.confidence,
        model=answer.model,
        citations=[CitationRead(**item) for item in citations],
    )


@router.post("/ask/stream")
async def ask_stream(payload: AskRequest, db: DB, user: CurrentUser) -> StreamingResponse:
    conversation, contexts, citations = await prepare_conversation(payload, db, user)
    question_message = AIMessage(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=payload.question,
        citations=[],
        confidence=None,
        model_name=None,
    )
    answer_message = AIMessage(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content="",
        citations=citations,
        confidence=None,
        model_name=None,
    )
    db.add_all([question_message, answer_message])
    await db.commit()
    await db.refresh(question_message)
    await db.refresh(answer_message)

    async def stream():
        full_answer = ""
        try:
            provider = get_rag_provider()
            yield json_event(
                "meta",
                {
                    "conversation_id": conversation.id,
                    "question_message_id": question_message.id,
                    "answer_message_id": answer_message.id,
                    "model": provider.model_name,
                    "citations": citations,
                },
            )
            for delta in provider.stream_answer(payload.question, contexts):
                full_answer += delta
                yield json_event("delta", {"text": delta})
            answer_message.content = full_answer
            answer_message.confidence = (
                round(sum(context.score for context in contexts) / len(contexts), 3)
                if contexts
                else 0.0
            )
            answer_message.model_name = provider.model_name
            await db.commit()
            yield json_event(
                "done",
                {
                    "answer": full_answer,
                    "confidence": answer_message.confidence,
                    "model": provider.model_name,
                    "citations": citations,
                },
            )
        except RAGProviderError as exc:
            answer_message.content = str(exc)
            answer_message.confidence = 0.0
            await db.commit()
            yield json_event(
                "error",
                {"code": "rag_provider_unavailable", "message": str(exc)},
            )

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.post("/messages/{message_id}/feedback", response_model=FeedbackRead)
async def submit_feedback(
    message_id: int, payload: FeedbackRequest, db: DB, user: CurrentUser
) -> FeedbackRead:
    message = await db.scalar(
        select(AIMessage)
        .join(AIConversation, AIConversation.id == AIMessage.conversation_id)
        .where(AIMessage.id == message_id, AIConversation.user_id == user.id)
        .options(selectinload(AIMessage.feedback))
    )
    if not message or message.role != MessageRole.ASSISTANT:
        raise AppError("message_not_found", "Assistant message does not exist", 404)
    feedback = message.feedback
    if feedback:
        feedback.rating = payload.rating
        feedback.comment = payload.comment
    else:
        feedback = AIFeedback(
            message_id=message.id,
            user_id=user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
        db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return FeedbackRead(
        id=feedback.id,
        message_id=feedback.message_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )
