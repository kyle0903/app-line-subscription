from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from schema.users import UserProfile
from models.users import User
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(
    database_url,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 取得db中的user
def get_user(line_id: str):
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.line_id == line_id).first()
            if user:
                return UserProfile(
                    line_id=user.line_id,
                    name=user.name,
                    status=user.status,
                    role=user.role,
                    group_id=user.group_id,
                    created_at=user.created_at,
                        updated_at=user.updated_at
                    )
            return None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

# 新增user
def create_user(user: UserProfile):
    try:
        with SessionLocal() as db:
            db.add(User(**user.model_dump()))
            db.commit()
            db.refresh(user)
            return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")

# 更新使用者狀態
def update_user_status(line_id: str, status: int):
    try:
        with SessionLocal() as db:        
            user = db.query(User).filter(User.line_id == line_id).first()
            user.status = status
            db.commit()
            db.refresh(user)
    except Exception as e:
        logger.error(f"Error updating user status: {e}")

