from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import datetime

from bot.keyboards import admin_menu_keyboard
from database.queries import (
    get_statistics, get_todays_appointments, get_all_doctors,
    cancel_appointment, add_doctor, toggle_doctor
)
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminState(StatesGroup):
    broadcast_message = State()
    adding_doctor_name = State()
    adding_doctor_specialty = State()
    adding_doctor_emoji = State()


# ===================== ADMIN PANEL =====================

@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    stats = await get_statistics()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangilash", callback_data="admin_stats")
    builder.button(text="⬅️ Admin menu", callback_data="back_admin")
    builder.adjust(2)

    text = (
        f"📊 Statistika\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 Jami navbatlar: {stats['total']}\n"
        f"📅 Bugungi navbatlar: {stats['today']}\n"
        f"⏳ Kutilayotgan: {stats['upcoming']}\n"
        f"❌ Bu oy bekor qilingan: {stats['cancelled_month']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_today")
async def admin_today_appointments(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    appointments = await get_todays_appointments()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Yangilash", callback_data="admin_today")
    builder.button(text="⬅️ Admin menu", callback_data="back_admin")
    builder.adjust(2)

    if not appointments:
        await callback.message.edit_text(
            f"📅 Bugungi navbatlar\n\n"
            f"Hozircha bugungi navbatlar yo'q.",
            reply_markup=builder.as_markup(),
        )
        return

    text = f"📅 Bugungi navbatlar ({len(appointments)} ta)\n\n"
    for i, apt in enumerate(appointments, 1):
        time_str = apt.appointment_datetime.strftime("%H:%M")
        text += (
            f"*{i}.* 🕐 {time_str}\n"
            f"   👤 {apt.patient_name}\n"
            f"   📞 {apt.patient_phone}\n"
            f"   👨‍⚕️ {apt.doctor_name}\n\n"
        )

    # Xabar juda uzun bo'lsa qisqartirish
    if len(text) > 4000:
        text = text[:4000] + "\n...(qolganlar)"

    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin_doctors")
async def admin_doctors(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    doctors = await get_all_doctors()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for doc in doctors:
        status = "✅" if doc.is_active else "❌"
        builder.button(
            text=f"{status} {doc.name}",
            callback_data=f"toggle_doc_{doc.id}"
        )

    builder.button(text="➕ Shifokor qo'shish", callback_data="add_doctor")
    builder.button(text="⬅️ Admin menu", callback_data="back_admin")
    builder.adjust(1)

    await callback.message.edit_text(
        "👨‍⚕️ Shifokorlar ro'yxati\n\n"
        "✅ = Faol | ❌ = Nofaol\n"
        "O'zgartirish uchun shifokor ustiga bosing:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("toggle_doc_"))
async def toggle_doctor_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    doctor_id = int(callback.data.split("_")[2])
    new_status = await toggle_doctor(doctor_id)

    status_text = "✅ Faollashtrildi" if new_status else "❌ O'chirildi"
    await callback.answer(status_text)
    await admin_doctors(callback)


@router.callback_query(F.data == "add_doctor")
async def start_add_doctor(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    await callback.message.edit_text(
        "➕ Yangi shifokor qo'shish\n\n"
        "Shifokorning to'liq ismini kiriting:\n"
        "(Misol: Karimov Jasur Aliyevich)",
    )
    await state.set_state(AdminState.adding_doctor_name)


@router.message(AdminState.adding_doctor_name)
async def doctor_name_entered(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.update_data(doctor_name=message.text.strip())
    await message.answer(
        "✅ Ism saqlandi.\n\n"
        "Mutaxassisligini kiriting:\n"
        "(Misol: Kardiolog, Terapevt, Stomatolog)"
    )
    await state.set_state(AdminState.adding_doctor_specialty)


@router.message(AdminState.adding_doctor_specialty)
async def doctor_specialty_entered(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.update_data(doctor_specialty=message.text.strip())
    await message.answer(
        "✅ Mutaxassislik saqlandi.\n\n"
        "Emoji tanlang (bir ta emoji yuboring):\n"
        "👨‍⚕️ 👩‍⚕️ ❤️ 🧠 🦷 👁️ 🦴 🩺"
    )
    await state.set_state(AdminState.adding_doctor_emoji)


@router.message(AdminState.adding_doctor_emoji)
async def doctor_emoji_entered(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    emoji = message.text.strip() or "👨‍⚕️"

    doctor = await add_doctor(
        name=data["doctor_name"],
        specialty=data["doctor_specialty"],
        emoji=emoji
    )

    await message.answer(
        f"✅ Shifokor muvaffaqiyatli qo'shildi!\n\n"
        f"{emoji} {doctor.name}\n"
        f"🩺 {doctor.specialty}",
        reply_markup=admin_menu_keyboard(),
    )
    await state.clear()


# ===================== XABAR YUBORISH =====================

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="back_admin")

    await callback.message.edit_text(
        "📢 Barcha mijozlarga xabar yuborish\n\n"
        "Yubormoqchi bo'lgan xabaringizni yozing:\n"
        "(Markdown format qo'llab-quvvatlanadi)",
        reply_markup=builder.as_markup(),
    )
    await state.set_state(AdminState.broadcast_message)


@router.message(AdminState.broadcast_message)
async def send_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    broadcast_text = message.text
    await state.clear()

    # Barcha mijozlarni topish
    from database.db import AsyncSessionLocal, Appointment
    from sqlalchemy import select, distinct

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(distinct(Appointment.patient_tg_id))
        )
        user_ids = result.scalars().all()

    sent = 0
    failed = 0

    await message.answer(f"📤 Xabar yuborilmoqda... ({len(user_ids)} ta foydalanuvchi)")

    for user_id in user_ids:
        try:
            await message.bot.send_message(
                user_id,
                f"📢 *{message.bot.username} dan xabar:*\n\n{broadcast_text}",
            )
            sent += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"✅ Yuborildi: {sent} ta\n"
        f"❌ Yuborilmadi: {failed} ta",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == "back_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "⚙️ Admin panel",
        reply_markup=admin_menu_keyboard(),
    )
