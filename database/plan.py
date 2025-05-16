from typing import List
from database.models import Comment, Plan, User, Task, user_plans
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

def add_comment_to_task(
    task_id: str,
    author_telegram_id: int,
    comment_text: str
) -> Comment:
    try:
        with db.transaction():
            task = db.session.query(Task).filter(Task.id == task_id).first()
            if not task:
                raise ValueError("Task not found")
            
            user = db.session.query(User).filter(User.telegram_id == author_telegram_id).first()
            if not user:
                raise ValueError("User not found")
            
            comment = Comment(
                task_id=task_id,
                author_id=user.id,
                body=comment_text
            )
            
            db.session.add(comment)
            db.session.flush()
            db.session.refresh(comment)
            
            return comment
            
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        db.session.rollback()
        raise

def publish_user_plan(telegram_id: int, plan_id: str) -> bool:
    try:
        with db.transaction():
            user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.error(f"User with telegram_id {telegram_id} not found")
                return False
            
            plan = db.session.query(Plan)\
                .filter(Plan.id == plan_id)\
                .first()
            
            if plan:
                user.published_plan = plan
                db.session.commit()
                return True

            plan = db.session.query(Plan).filter(~Plan.users.any()).filter(Plan.id == plan_id).all()

            if not plan:
                logger.error(f"Plan {plan_id} not found or doesn't belong to user {telegram_id}")
                return False
            
            
            
    except Exception as e:
        logger.error(f"Error publishing plan: {e}")
        db.session.rollback()
        return False
    

def get_published_plan(telegram_id: int) -> Plan | None:
    try:
        user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
        return user.published_plan if user else None
    except Exception as e:
        logger.error(f"Error getting published plan: {e}")
        return None

def unpublish_user_plan(telegram_id: int) -> bool:
    try:
        with db.transaction():
            user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user or not user.published_plan_id:
                return False
            
            user.published_plan = None
            return True
    except Exception as e:
        logger.error(f"Error unpublishing plan: {e}")
        db.session.rollback()
        return False

def get_user_published_plans() -> List[tuple[User, Plan]]:
    try:
        return db.session.query(User, Plan)\
            .join(Plan, User.published_plan_id == Plan.id)\
            .all()
    except Exception as e:
        logger.error(f"Error getting published plans: {e}")
        return []
    
def delete_user_plan(telegram_id: int, plan_id: str) -> bool:
    try:
        with db.transaction():
            user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                logger.error(f"User with telegram_id {telegram_id} not found")
                return False
            
            plan = db.session.query(Plan)\
                .join(user_plans, Plan.id == user_plans.c.plan_id)\
                .filter(Plan.id == plan_id)\
                .filter(user_plans.c.user_id == user.id)\
                .first()
            
            if not plan:
                logger.error(f"Plan {plan_id} not found or doesn't belong to user {telegram_id}")
                return False
            
            if user.current_plan_id == plan.id:
                user.current_plan = None
            if user.published_plan_id == plan.id:
                user.published_plan = None
            
            db.session.query(Task).filter(Task.plan_id == plan.id).delete()
            db.session.query(Comment).filter(Comment.task_id.in_(
                db.session.query(Task.id).filter(Task.plan_id == plan.id)
            )).delete()
            
            db.session.execute(
                user_plans.delete().where(user_plans.c.plan_id == plan.id)
            )
            
            db.session.delete(plan)
            db.session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error deleting plan: {e}")
        db.session.rollback()
        return False
    
def reset_plan(plan_id: str) -> bool:
    try:
        with db.transaction():
            db.session.query(Task)\
                .filter(Task.plan_id == plan_id)\
                .update({Task.checked: False}, synchronize_session=False)
            
            db.session.query(Comment)\
                .filter(Comment.task_id.in_(
                    db.session.query(Task.id).filter(Task.plan_id == plan_id)
                )).delete(synchronize_session=False)
            
            db.session.commit()
            return True
            
    except Exception as e:
        logger.error(f"Error resetting plan {plan_id}: {e}")
        db.session.rollback()
        return False