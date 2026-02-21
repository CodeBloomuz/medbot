from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from datetime import date
from typing import List

from database.db import Doctor, Appointment


def doctors_keyboard(doctors: List[Doctor]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for doc in doctors:
        builder.button(
            text=f"{doc.emoji} {doc.name} — {doc.specialty}",
            callback_data=f"doc_{doc.id}"
        )
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def dates_keyboard(available_dates: List[date]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    day_names = {1: "Dush", 2: "Sesh", 3: "Chor", 4: "Pay", 5: "Jum", 6: "Shan", 7: "Yak"}
    month_names = {
        1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel",
        5: "May", 6: "Iyun", 7: "Iyul", 8: "Avgust",
        9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
    }

    for d in available_dates:
        day_name = day_names.get(d.isoweekday(), "")
        month_name = month_names.get(d.month, "")
        builder.button(
            text=f"📅 {d.day} {month_name} ({day_name})",
            callback_data=f"date_{d.strftime('%Y-%m-%d')}"
        )

    builder.button(text="⬅️ Orqaga", callback_data="back_to_doctors")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(2, repeat=True)
    return builder.as_markup()


def times_keyboard(slots: List[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.button(text=f"🕐 {slot}", callback_data=f"time_{slot}")
    builder.button(text="⬅️ Orqaga", callback_data="back_to_dates")
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    builder.adjust(3, repeat=True)
    return builder.as_markup()


def confirm_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, to'g'ri", callback_data=f"confirm_{appointment_id}")
    builder.button(text="🔄 Qaytadan", callback_data="restart")
    builder.adjust(2)
    return builder.as_markup()


def my_appointments_keyboard(appointments: List[Appointment]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for apt in appointments:
        date_str = apt.appointment_datetime.strftime("%d.%m %H:%M")
        builder.button(
            text=f"🗓 {date_str} — {apt.doctor_specialty}",
            callback_data=f"apt_{apt.id}"
        )
    builder.button(text="⬅️ Bosh menu", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def appointment_detail_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Navbatni bekor qilish", callback_data=f"cancel_apt_{appointment_id}")
    builder.button(text="⬅️ Orqaga", callback_data="my_appointments")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Navbat olish", callback_data="book_appointment")
    builder.button(text="🗓 Mening navbatlarim", callback_data="my_appointments")
    builder.button(text="📞 Klinika ma'lumotlari", callback_data="clinic_info")
    builder.adjust(1)
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="📋 Bugungi navbatlar", callback_data="admin_today")
    builder.button(text="👨‍⚕️ Shifokorlar", callback_data="admin_doctors")
    builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    builder.adjust(2)
    return builder.as_markup()


def phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Raqamni yuborish", request_contact=True))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
