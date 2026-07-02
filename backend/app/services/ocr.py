import base64

import httpx

from app.core.config import settings


class OCRServiceError(RuntimeError):
    pass


class QwenOCRService:
    def __init__(
        self,
        *,
        enabled: bool = settings.qwen_ocr_enabled,
        api_key: str | None = settings.qwen_ocr_api_key or settings.openai_api_key,
        base_url: str = settings.qwen_ocr_base_url,
        model: str = settings.qwen_ocr_model,
        timeout_seconds: int = settings.qwen_ocr_timeout_seconds,
    ) -> None:
        self.enabled = enabled
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def recognize(self, image: bytes, mime_type: str) -> str:
        if not self.enabled:
            return ""
        if not self.api_key:
            raise OCRServiceError("QWEN_OCR_API_KEY is not configured")
        data_url = f"data:{mime_type};base64,{base64.b64encode(image).decode('ascii')}"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "请对图片进行OCR识别，并提取图片中的文字、表格、数字、标题、"
                                "图表含义和关键视觉信息。请用中文输出，保留原始关键内容。"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        try:
            response = httpx.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OCRServiceError(f"Qwen OCR request failed: {exc}") from exc
        text = self._extract_text(response.json())
        if not text:
            raise OCRServiceError("Qwen OCR returned an empty response")
        return text

    def _extract_text(self, data: dict[str, object]) -> str:
        choices = data.get("choices")
        if isinstance(choices, list):
            parts: list[str] = []
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        parts.append(content)
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and isinstance(block.get("text"), str):
                                parts.append(block["text"])
                text = choice.get("text")
                if isinstance(text, str):
                    parts.append(text)
            if parts:
                return "\n".join(parts).strip()
        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text.strip()
        return ""


def get_ocr_service() -> QwenOCRService:
    return QwenOCRService()
