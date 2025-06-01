import random
from schema.users import UserProfile
from schema.enums import UserState, Action


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

def action_message(text, user: UserProfile):
    if text == Action.CREATE:
        # 設置用戶狀態為等待輸入訂閱名稱
        user.status = UserState.WAITING_FOR_NAME
        return "請輸入訂閱名稱："
    elif user.status == UserState.WAITING_FOR_NAME:
        # 用戶已輸入訂閱名稱，產生訂閱碼
        subscription_name = text
        # 隨機產生四位數字和兩位英文字母
        random_number = generate_invite_code()
        # 清除用戶狀態
        user.status = 0
        return f"訂閱名稱：{subscription_name}\n您的群組邀請碼為：{random_number}"
    else:
        return f"您傳送了: " + text