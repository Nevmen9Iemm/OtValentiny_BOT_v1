from aiogram import Router
from aiogram.types import Message

user_private_router = Router()

@user_private_router.message(commands=["start"])
async def start_command(message: Message):
    await message.answer("Ласкаво просимо до OtValentiny!")