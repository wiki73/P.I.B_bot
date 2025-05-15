from models import User
from database.database import db

def create_user(telegram_id: int, name: str) -> User:
    user = User(
        telegram_id=telegram_id,
        name=name
    )
    with db.transaction():
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
    return user

def get_user_by_telegram_id(telegram_id: int) -> User | None:
    return db.session.query(User).filter(User.telegram_id == telegram_id).first()

def save_user(telegram_id: int, name: str) -> User:
    user = get_user_by_telegram_id(telegram_id)
    
    if user:
        with db.transaction():
            user.name = name
            db.session.commit()
            db.session.refresh(user)
        return user
    
    return create_user(telegram_id, name) 