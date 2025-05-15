from typing import List
from models import Statistic, Task, User
from database.database import db
import logging

logger = logging.getLogger(__name__)

def create_statistic(
    user_id: str,
    plan_id: str,
    total_tasks: int,
    completed_tasks: int,
    study_hours: float
) -> Statistic:
    try:
        with db.transaction():

            user = db.session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            statistic = Statistic(
                user_id=user.id,
                plan_id=plan_id,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                study_hours=study_hours
            )
            db.session.add(statistic)
            db.session.commit()
            return statistic
    except Exception as e:
        logger.error(f"Error creating statistic: {e}")
        db.session.rollback()
        raise

def update_statistic(
    statistic_id: str,
    total_tasks: int = None,
    completed_tasks: int = None,
    study_hours: float | None = None
) -> bool:
    try:
        with db.transaction():
            statistic = db.session.query(Statistic).filter(Statistic.id == statistic_id).first()
            if not statistic:
                return False
            
            if total_tasks is not None:
                statistic.total_tasks = total_tasks
            if completed_tasks is not None:
                statistic.completed_tasks = completed_tasks
            if study_hours is not None:
                statistic.study_hours = study_hours
                
            db.session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating statistic: {e}")
        db.session.rollback()
        return False

def get_user_statistics(telegram_id: int) -> List[Statistic]:
    try:
        user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return []
            
        return db.session.query(Statistic)\
            .filter(Statistic.user_id == user.id)\
            .order_by(Statistic.created_at.desc())\
            .all()
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return []

def get_plan_statistics(plan_id: str) -> List[Statistic]:
    try:
        return db.session.query(Statistic)\
            .filter(Statistic.plan_id == plan_id)\
            .order_by(Statistic.created_at.desc())\
            .all()
    except Exception as e:
        logger.error(f"Error getting plan statistics: {e}")
        return []

def get_statistic_by_id(statistic_id: str) -> Statistic | None:
    try:
        return db.session.query(Statistic).filter(Statistic.id == statistic_id).first()
    except Exception as e:
        logger.error(f"Error getting statistic by id: {e}")
        return None

def delete_statistic(statistic_id: str) -> bool:
    try:
        with db.transaction():
            statistic = db.session.query(Statistic).filter(Statistic.id == statistic_id).first()
            if not statistic:
                return False
                
            db.session.delete(statistic)
            db.session.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting statistic: {e}")
        db.session.rollback()
        return False
    
def calculate_plan_progress(plan_id: str) -> dict:
    try:
        tasks = db.session.query(Task).filter(Task.plan_id == plan_id).all()
        if not tasks:
            return {"total": 0, "completed": 0, "percentage": 0}
            
        total = len(tasks)
        completed = sum(1 for task in tasks if task.checked)
        percentage = (completed / total) * 100 if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "percentage": round(percentage, 2)
        }
    except Exception as e:
        logger.error(f"Error calculating plan progress: {e}")
        return {"total": 0, "completed": 0, "percentage": 0}

def update_plan_statistics(telegram_id: int, plan_id: str, study_hours: float = 0) -> bool:
    try:
        with db.transaction():
            user = db.session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
                
            progress = calculate_plan_progress(plan_id)
            
            statistic = db.session.query(Statistic)\
                .filter(Statistic.user_id == user.id)\
                .filter(Statistic.plan_id == plan_id)\
                .order_by(Statistic.created_at.desc())\
                .first()
                
            if statistic:
                statistic.total_tasks = progress["total"]
                statistic.completed_tasks = progress["completed"]
                statistic.study_hours += study_hours
            else:
                statistic = Statistic(
                    user_id=user.id,
                    plan_id=plan_id,
                    total_tasks=progress["total"],
                    completed_tasks=progress["completed"],
                    study_hours=study_hours
                )
                db.session.add(statistic)
                
            db.session.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating plan statistics: {e}")
        db.session.rollback()
        return False