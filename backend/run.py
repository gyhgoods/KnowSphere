import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=os.getenv("KNOWSPHERE_HOST", "127.0.0.1"),
        port=int(os.getenv("KNOWSPHERE_PORT", "8000")),
        reload=os.getenv("KNOWSPHERE_RELOAD", "false").lower() == "true",
    )


if __name__ == "__main__":
    main()
