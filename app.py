import requests
import json
import os
import hmac
import hashlib
import base64
import random
import string
from fastapi import FastAPI, Request, Header, HTTPException, Response
from typing import Optional
from dotenv import load_dotenv
import uvicorn
import logging
from utils import action_message
from datetime import datetime
from schema.users import UserProfile
from schema.enums import UserRole
from db import get_user, create_user
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
import uuid

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# LINE 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(
    access_token=LINE_CHANNEL_ACCESS_TOKEN
)

client = ApiClient(configuration)
messaging_api = MessagingApi(client)


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
        # 驗證 LINE 簽名
        if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
            logger.error("LINE credentials not configured")
            raise HTTPException(status_code=500, detail="LINE credentials not configured")
        
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # 驗證簽名
        if x_line_signature:
            hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body_str.encode('utf-8'), hashlib.sha256).digest()
            signature = base64.b64encode(hash).decode('utf-8')
            
            if signature != x_line_signature:
                logger.error("Invalid signature")
                raise HTTPException(status_code=400, detail="Invalid signature")
        
        # 解析 webhook 數據
        events = json.loads(body_str)["events"]
        
        for event in events:
            # 處理不同類型的事件
            event_type = event.get("type")
            
            if event_type == "message":
                # 處理訊息事件
                message_type = event.get("message", {}).get("type")
                reply_token = event.get("replyToken")
                user_id = event.get("source").get("userId")
                username = messaging_api.get_profile(user_id).display_name
                user_info = UserProfile(
                    line_id=user_id,
                    name=username,
                    status=0,
                    role=UserRole.ADMIN,
                    group_id=uuid.uuid4(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                user = get_user(user_id)
                if user is None:
                    user = create_user(user_info)
                if message_type == "text":
                    text = event.get("message", {}).get("text", "")
                    action_text = action_message(text, user)
                    await reply_message(reply_token, [{
                        "type": "text",
                        "text": action_text
                    }])
        
        return Response(content="OK", media_type="text/plain")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response(content="OK", media_type="text/plain")

async def reply_message(reply_token, messages):
    """發送回覆訊息到 LINE"""
    try:
        url = 'https://api.line.me/v2/bot/message/reply'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        data = {
            'replyToken': reply_token,
            'messages': messages
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logger.error(f"Error sending reply: {response.text}")
    except Exception as e:
        logger.error(f"Error in reply_message: {e}")

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