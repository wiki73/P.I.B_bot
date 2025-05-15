from typing import List
from models import Plan, User, Task
from database.database import db
import logging

logger = logging.getLogger(__name__)

def get_base_plans() -> List[Plan]:
    return db.session.query(Plan).filter(~Plan.users.any()).all()

def get_user_plans(user_id: str) -> List[Plan]:
    try:
        with db.transaction():
            return db.session.query(Plan).filter(Plan.users.any(User.telegram_id == user_id)).all()
    except Exception as e:
        logger.error(f"Error getting user plans: {e}")
        db.refresh_session()
        return []

def create_base_plan(name: str) -> Plan:
    plan = Plan(name=name)
    with db.transaction():
        db.session.add(plan)
        db.session.refresh(plan)
    return plan

def create_user_plan(name: str, user_id: str, tasks_text: str = None) -> Plan:
    try:
        with db.transaction():
            user = db.session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                raise ValueError("User not found")
                
            plan = Plan(name=name)
            plan.users.append(user)
            db.session.add(plan)
            db.session.flush()
            
            if tasks_text:
                tasks = [task.strip() for task in tasks_text.split('\n') if task.strip()]
                for task_body in tasks:
                    task = Task(
                        plan_id=plan.id,
                        body=task_body
                    )
                    db.session.add(task)
            
            db.session.commit()
            return plan
            
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.session.rollback()
        raise
def get_current_plan(telegram_id: int) -> Plan | None:
    user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
    return user.current_plan if user else None

def set_current_plan(telegram_id: int, plan_id: str) -> bool:
    with db.transaction():
        user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return False
            
        plan = db.session.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            return False
            
        user.current_plan = plan
        return True

def add_task_to_plan(plan_id: str, task_body: str) -> Task:
    task = Task(plan_id=plan_id, body=task_body)
    with db.transaction():
        db.session.add(task)
        db.session.refresh(task)
    return task

def get_plan_tasks(plan_id: str) -> List[Task]:
    return db.session.query(Task).filter(Task.plan_id == plan_id).all()

def update_task(task_id: str, new_body: str) -> bool:
    with db.transaction():
        task = db.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        task.body = new_body
        return True

def delete_task(task_id: str) -> bool:
    with db.transaction():
        task = db.session.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        db.session.delete(task)
        return True  
