from fastapi import FastAPI, Request, Header, Response
from typing import Optional
import uvicorn
from utils import process_webhook
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.head("/")
async def head():
    return {"message": "Hello World"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/webhook")
async def line_webhook(request: Request, x_line_signature: Optional[str] = Header(None)):
    try:
        return await process_webhook(request, x_line_signature)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response(content="OK", media_type="text/plain")


if __name__ == "__main__":
    # 使用 uvicorn 運行應用
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile=None,  # 本地開發不需要 SSL
        ssl_certfile=None
    )