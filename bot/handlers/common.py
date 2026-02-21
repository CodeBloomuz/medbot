from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.keyboards import main_menu_keyboard
from config import CLINIC_NAME, CLINIC_ADDRESS, CLINIC_PHONE, ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    name = message.from_user.first_name or "Mehmon"

    text = (
        f"👋 Assalomu alaykum, {name}!\n\n"
        f"🏥 {CLINIC_NAME} Telegram botiga xush kelibsiz!\n\n"
        f"Bu bot orqali siz:\n"
        f"✅ Shifokorga navbat olishingiz\n"
        f"📋 Navbatlaringizni ko'rishingiz\n"
        f"🔔 Eslatmalar olishingiz mumkin\n\n"
        f"Quyidan kerakli bo'limni tanlang:"
    )

    await message.answer(text, reply_markup=main_menu_keyboard())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏥 Bosh menu:",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏥 Bosh menu:",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "clinic_info")
async def clinic_info(callback: CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="main_menu")

    text = (
        f"🏥 {CLINIC_NAME}\n\n"
        f"📍 Manzil: {CLINIC_ADDRESS}\n"
        f"📞 Telefon: {CLINIC_PHONE}\n"
        f"🕐 Ish vaqti: Dush-Jum 09:00 - 18:00\n\n"
        f"Navbat olish uchun '📋 Navbat olish' tugmasini bosing."
    )

    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi.\n\nBosh menuga qaytish uchun /menu",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "restart")
async def restart_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    # Book appointment ni qayta ishga tushirish
    from bot.handlers.patient import start_booking
    await start_booking(callback, state)


@router.message(Command("admin"))
async def admin_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Sizda admin huquqlari yo'q.")
        return
    from bot.keyboards import admin_menu_keyboard
    await message.answer(
        "⚙️ Admin panel\n\nKerakli bo'limni tanlang:",
        reply_markup=admin_menu_keyboard(),
    )
