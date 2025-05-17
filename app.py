from fastapi import FastAPI, Request, Header, HTTPException, Response
import uvicorn
import json
from typing import Optional
import os
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# LINE 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/webhook")
async def line_webhook(request: Request, x_line_signature: Optional[str] = Header(None)):
    # 驗證 LINE 簽名
    if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="LINE credentials not configured")
    
    body = await request.body()
    body_str = body.decode('utf-8')
    
    # 驗證簽名
    if x_line_signature:
        hash = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body_str.encode('utf-8'), hashlib.sha256).digest()
        signature = base64.b64encode(hash).decode('utf-8')
        
        if signature != x_line_signature:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    # 解析 webhook 數據
    try:
        events = json.loads(body_str)["events"]
        
        for event in events:
            # 處理不同類型的事件
            event_type = event.get("type")
            
            if event_type == "message":
                # 處理訊息事件
                message_type = event.get("message", {}).get("type")
                reply_token = event.get("replyToken")
                
                if message_type == "text":
                    text = event.get("message", {}).get("text", "")
                    # 處理文字訊息，根據內容回覆
                    await reply_message(reply_token, [{
                        "type": "text",
                        "text": f"您傳送了: {text}"
                    }])
            
            # 可以擴展處理其他事件類型，如: follow, unfollow, join, leave, postback 等
        
        return Response(content="OK", media_type="text/plain")
    
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return Response(content="OK", media_type="text/plain")

async def reply_message(reply_token, messages):
    """發送回覆訊息到 LINE"""
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
        print(f"Error sending reply: {response.text}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)