from database.models import init_db, Base, Plan, Task, engine
from database.database import db

def create_default_plans():
    default_plans = [
        ("Стандартный день", "Утро:\n- Зарядка\n- Завтрак\n\nРабота:\n- Важные задачи\n- Встречи\n\nВечер:\n- Отдых\n- Подготовка к следующему дню"),
        ("Продуктивный день", "Утро:\n- Медитация\n- Планирование дня\n\nРабота:\n- Сложные задачи\n- Обучение\n\nВечер:\n- Анализ дня\n- Чтение"),
        ("Выходной день", "Утро:\n- Долгий завтрак\n- Прогулка\n\nДень:\n- Хобби\n- Встречи с друзьями\n\nВечер:\n- Кино\n- Ранний сон")
    ]
    
    with db.transaction():
        existing_plans = db.session.query(Plan).filter(~Plan.users.any()).all()
        if not existing_plans:
            for name, tasks in default_plans:
                plan = Plan(name=name)
                db.session.add(plan)
                db.session.flush()
                
                tasks_list = [task.strip('- ') for task in tasks.split('\n') if task.strip().startswith('-')]
                for task_text in tasks_list:
                    task = Task(plan_id=plan.id, body=task_text)
                    db.session.add(task)

if __name__ == "__main__":
    print("Initializing database...")
    init_db() 
    print("Creating default plans...")
    create_default_plans()
    print("Database initialized successfully!") 