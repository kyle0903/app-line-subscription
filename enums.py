from enum import Enum

class Action(str, Enum):
    CREATE = "創建訂閱群組"
    JOIN = "加入訂閱群組"
    LEAVE = "離開訂閱群組"
    LIST = "查看訂閱群組"
    HELP = "查看幫助"

class UserState(str, Enum):
    WAITING_FOR_NAME = "等待輸入訂閱名稱"
    WAITING_FOR_CODE = "等待輸入邀請碼"
