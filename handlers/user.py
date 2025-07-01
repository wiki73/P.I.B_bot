from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.plan import get_user_plans
from keyboards.inline import create_plan_keyboard, plans_keyboard
from states.plans import PlanCreation
from utils import logger
from database.database import db

router = Router()


@router.callback_query(F.data == "view_user_plans")
async def handle_show_user_plans(callback: CallbackQuery):
    try:
        db.refresh_session()

        user_plans = get_user_plans(callback.from_user.id)

        if not user_plans:
            await callback.message.edit_text(
                "У вас пока нет сохранённых планов.",
                reply_markup=create_plan_keyboard(),
            )
            return

        await callback.message.edit_text(
            "📁 Ваши планы:", reply_markup=plans_keyboard(user_plans, "user")
        )
    except Exception as e:
        logger.error(f"Ошибка при показе планов: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при загрузке планов. Попробуйте позже.",
            reply_markup=create_plan_keyboard(),
        )
    finally:
        await callback.answer()


@router.callback_query(F.data == "create_plan")
async def create_plan_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите название для нового плана:", reply_markup=create_plan_keyboard()
    )
    await state.set_state(PlanCreation.waiting_for_title)
    await callback.answer()
