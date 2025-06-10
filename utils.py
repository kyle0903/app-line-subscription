from fastapi import HTTPException
import random
from schema.users import UserProfile
from schema.enums import Action, UserRole
import logging
from dotenv import load_dotenv
import os
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
import requests
import json
import hmac
import hashlib
import base64
from datetime import datetime
from db import get_user, create_user, update_user_status
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


async def process_webhook(request, x_line_signature):
    # 驗證 LINE 簽名
    if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
        logger.error("LINE credentials not configured")
        raise HTTPException(status_code=400, detail="LINE credentials not configured")
    
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
                await reply_message(reply_token, [{
                    "type": "text",
                    "text": action_message(text, user)
                }])

def action_message(text, user: UserProfile):
    if text == Action.CREATE:
        # 設置用戶狀態為等待輸入訂閱名稱
        update_user_status(user.line_id, 1)
        return "請輸入訂閱名稱："
    elif user.status == 1:
        # 用戶已輸入訂閱名稱，產生訂閱碼
        subscription_name = text
        # 隨機產生四位數字和兩位英文字母
        random_number = generate_invite_code()
        # 清除用戶狀態
        update_user_status(user.line_id, 0)
        return f"訂閱名稱：{subscription_name}\n您的群組邀請碼為：{random_number}"
    else:
        return f"您傳送了: " + text
    
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