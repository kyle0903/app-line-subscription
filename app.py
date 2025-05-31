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
import random
import string

# 載入環境變數
load_dotenv()

# LINE 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

app = FastAPI()

# 用於儲存用戶狀態的字典
user_states = {}

@app.head("/")
async def head():
    return {"message": "Hello World"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

def generate_invite_code(length=8):
    """
    生成邀請碼
    - 使用大寫字母和數字
    - 排除容易混淆的字符 (0, O, 1, I)
    - 確保至少包含一個字母和一個數字
    """
    # 定義可用字符
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # 排除 O, I
    digits = '23456789'  # 排除 0, 1
    
    # 確保至少有一個字母和一個數字
    code = [
        random.choice(letters),  # 至少一個字母
        random.choice(digits),   # 至少一個數字
    ]
    
    # 填充剩餘位置
    all_chars = letters + digits
    code.extend(random.choices(all_chars, k=length-2))
    
    # 打亂順序
    random.shuffle(code)
    
    return ''.join(code)

def action_message(text, user_id):
    if text == "/create":
        # 設置用戶狀態為等待輸入訂閱名稱
        user_states[user_id] = "waiting_for_name"
        return "請輸入訂閱名稱："
    elif user_id in user_states and user_states[user_id] == "waiting_for_name":
        # 用戶已輸入訂閱名稱，產生訂閱碼
        subscription_name = text
        # 隨機產生四位數字和兩位英文字母
        random_number = ''.join(random.choices(string.digits, k=4))
        random_letter = ''.join(random.choices(string.ascii_letters, k=2))
        # 清除用戶狀態
        del user_states[user_id]
        return f"訂閱名稱：{subscription_name}\n訂閱碼：{random_number}{random_letter}"
    else:
        return f"{user_id}您傳送了: " + text

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
                user_id = event.get("source").get("userId")
                
                if message_type == "text":
                    text = event.get("message", {}).get("text", "")
                    action_text = action_message(text, user_id)
                    await reply_message(reply_token, [{
                        "type": "text",
                        "text": action_text
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