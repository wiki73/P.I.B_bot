from aiogram import BaseMiddleware
from utils import logger

class StateLoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        state = data.get('state')
        if state:
            current_state = await state.get_state()
            logger.info(f"Current state before handler: {current_state}")
        
        result = await handler(event, data)

        if state:
            new_state = await state.get_state()
            logger.info(f"State after handler: {new_state}")
        
        return result
