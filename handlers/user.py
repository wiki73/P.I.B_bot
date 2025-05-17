from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.plan import get_user_plans
from database.user import save_user
from keyboards.inline import create_plan_keyboard, plans_keyboard
from states.plans import PlanCreation
from states.user import UserState
from utils import send_message_with_keyboard, show_main_menu, logger
from database.database import db

router = Router()

@router.message(UserState.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_name = message.text
        logger.info(f'Processing nickname for user {user_id}: {user_name}')
        
        user = save_user(user_id, user_name)
        logger.info(f'User saved: {user}')
        
        await send_message_with_keyboard(message, f"Отлично, {user_name}!")
        logger.info('Sent welcome message')
        
        await send_message_with_keyboard(message, f"Чем могу помочь?")
        logger.info('Sent help message')
        
        await show_main_menu(message)
        logger.info('Showed main menu')
        
        await state.clear()
        logger.info('State cleared')
    except Exception as e:
        logger.error(f'Error in process_nickname: {str(e)}')
        await send_message_with_keyboard(message, "Произошла ошибка при сохранении имени. Попробуйте еще раз или обратитесь к администратору.")

@router.callback_query(F.data == "view_user_plans")
async def handle_show_user_plans(callback: CallbackQuery):
    try:
        db.refresh_session()
        
        user_plans = get_user_plans(callback.from_user.id)
        
        if not user_plans:
            await callback.message.edit_text(
                "У вас пока нет сохранённых планов.",
                reply_markup=create_plan_keyboard()
            )
            return
        
        await callback.message.edit_text(
            "📁 Ваши планы:",
            reply_markup=plans_keyboard(user_plans, 'user')
        )
    except Exception as e:
        logger.error(f"Ошибка при показе планов: {e}")
        await callback.message.edit_text(
            "Произошла ошибка при загрузке планов. Попробуйте позже.",
            reply_markup=create_plan_keyboard()
        )
    finally:
        await callback.answer()

@router.callback_query(F.data == 'create_plan')
async def create_plan_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите название для нового плана:",
        reply_markup=create_plan_keyboard()
    )
    await state.set_state(PlanCreation.waiting_for_title)
    await callback.answer()