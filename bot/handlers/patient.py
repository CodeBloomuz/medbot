from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date

from bot.keyboards import (
    doctors_keyboard, dates_keyboard, times_keyboard,
    main_menu_keyboard, my_appointments_keyboard,
    appointment_detail_keyboard, phone_keyboard
)
from database.queries import (
    get_all_doctors, get_doctor_by_id, get_available_dates,
    get_available_slots, create_appointment, get_patient_appointments,
    cancel_appointment
)
from config import CLINIC_NAME, CLINIC_ADDRESS, ADMIN_IDS

router = Router()


class BookingState(StatesGroup):
    choosing_doctor = State()
    choosing_date = State()
    choosing_time = State()
    entering_name = State()
    entering_phone = State()
    confirming = State()


# ===================== NAVBAT OLISH =====================

@router.callback_query(F.data == "book_appointment")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    doctors = await get_all_doctors()

    if not doctors:
        await callback.message.edit_text(
            "😔 Hozircha shifokorlar ro'yxati bo'sh.\nIltimos, keyinroq urinib ko'ring.",
            reply_markup=main_menu_keyboard()
        )
        return

    await callback.message.edit_text(
        "👨‍⚕️ *Shifokorni tanlang:*",
        reply_markup=doctors_keyboard(doctors),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.choosing_doctor)


@router.callback_query(BookingState.choosing_doctor, F.data.startswith("doc_"))
async def doctor_chosen(callback: CallbackQuery, state: FSMContext):
    doctor_id = int(callback.data.split("_")[1])
    doctor = await get_doctor_by_id(doctor_id)

    if not doctor:
        await callback.answer("Shifokor topilmadi!", show_alert=True)
        return

    await state.update_data(doctor_id=doctor_id, doctor_name=doctor.name)

    available_dates = await get_available_dates(doctor_id)

    if not available_dates:
        await callback.message.edit_text(
            f"😔 *{doctor.name}* uchun hozircha bo'sh kunlar yo'q.\n"
            f"Boshqa shifokorni tanlang yoki keyinroq urinib ko'ring.",
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    await callback.message.edit_text(
        f"✅ Shifokor: *{doctor.name}* ({doctor.specialty})\n\n"
        f"📅 *Qulay kunni tanlang:*",
        reply_markup=dates_keyboard(available_dates),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.choosing_date)


@router.callback_query(BookingState.choosing_date, F.data == "back_to_doctors")
async def back_to_doctors(callback: CallbackQuery, state: FSMContext):
    doctors = await get_all_doctors()
    await callback.message.edit_text(
        "👨‍⚕️ *Shifokorni tanlang:*",
        reply_markup=doctors_keyboard(doctors),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.choosing_doctor)


@router.callback_query(BookingState.choosing_date, F.data.startswith("date_"))
async def date_chosen(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split("_")[1]
    chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    data = await state.get_data()
    slots = await get_available_slots(data["doctor_id"], chosen_date)

    if not slots:
        await callback.answer("Bu kunda bo'sh vaqt yo'q, boshqa kun tanlang!", show_alert=True)
        return

    await state.update_data(chosen_date=date_str)

    day_names = {1: "Dushanba", 2: "Seshanba", 3: "Chorshanba",
                 4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba"}

    await callback.message.edit_text(
        f"📅 Sana: *{chosen_date.day}.{chosen_date.month:02d}.{chosen_date.year}* "
        f"({day_names.get(chosen_date.isoweekday(), '')})\n\n"
        f"🕐 *Qulay vaqtni tanlang:*",
        reply_markup=times_keyboard(slots),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.choosing_time)


@router.callback_query(BookingState.choosing_time, F.data == "back_to_dates")
async def back_to_dates(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    available_dates = await get_available_dates(data["doctor_id"])
    await callback.message.edit_text(
        "📅 *Qulay kunni tanlang:*",
        reply_markup=dates_keyboard(available_dates),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.choosing_date)


@router.callback_query(BookingState.choosing_time, F.data.startswith("time_"))
async def time_chosen(callback: CallbackQuery, state: FSMContext):
    time_str = callback.data.split("_")[1]
    await state.update_data(chosen_time=time_str)

    await callback.message.edit_text(
        "👤 *Ismingizni kiriting:*\n\n"
        "_(To'liq ism sharifingizni yozing)_",
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.entering_name)


@router.message(BookingState.entering_name)
async def name_entered(message: Message, state: FSMContext):
    name = message.text.strip()

    if len(name) < 3:
        await message.answer("❌ Iltimos, to'liq ismingizni kiriting (kamida 3 harf).")
        return

    await state.update_data(patient_name=name)

    await message.answer(
        f"✅ Ism: *{name}*\n\n"
        f"📞 *Telefon raqamingizni kiriting:*\n"
        f"_(Misol: +998901234567)_\n\n"
        f"Yoki tugmani bosing:",
        reply_markup=phone_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(BookingState.entering_phone)


@router.message(BookingState.entering_phone, F.contact)
async def phone_from_contact(message: Message, state: FSMContext):
    """Kontakt orqali telefon raqami"""
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await process_phone(message, state, phone)


@router.message(BookingState.entering_phone)
async def phone_entered(message: Message, state: FSMContext):
    """Qo'lda kiritilgan telefon raqami"""
    phone = message.text.strip().replace(" ", "").replace("-", "")

    # Tekshirish
    if not (phone.startswith("+998") or phone.startswith("998") or phone.startswith("0")):
        await message.answer(
            "❌ Noto'g'ri format. Iltimos qaytadan kiriting:\n"
            "_(Misol: +998901234567 yoki 901234567)_",
            parse_mode="Markdown"
        )
        return

    if phone.startswith("0"):
        phone = "+998" + phone[1:]
    elif phone.startswith("998"):
        phone = "+" + phone

    await process_phone(message, state, phone)


async def process_phone(message: Message, state: FSMContext, phone: str):
    from aiogram.types import ReplyKeyboardRemove
    await state.update_data(patient_phone=phone)

    data = await state.get_data()
    chosen_date = datetime.strptime(data["chosen_date"], "%Y-%m-%d").date()

    # Tasdiqlash xabari
    confirm_text = (
        f"📋 *Navbat ma'lumotlari:*\n\n"
        f"👨‍⚕️ Shifokor: *{data['doctor_name']}*\n"
        f"📅 Sana: *{chosen_date.strftime('%d.%m.%Y')}*\n"
        f"🕐 Vaqt: *{data['chosen_time']}*\n"
        f"👤 Ism: *{data['patient_name']}*\n"
        f"📞 Telefon: *{phone}*\n\n"
        f"Ma'lumotlar to'g'rimi?"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, to'g'ri — Tasdiqlash", callback_data="do_confirm")
    builder.button(text="🔄 Qaytadan boshlash", callback_data="restart")
    builder.adjust(1)

    await message.answer(
        confirm_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    # Telefon klaviaturasini yashirish
    await message.answer("👆 Yuqoridagi tugmalardan birini tanlang.",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(BookingState.confirming)


@router.callback_query(BookingState.confirming, F.data == "do_confirm")
async def confirm_appointment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    chosen_date = datetime.strptime(data["chosen_date"], "%Y-%m-%d").date()

    appointment = await create_appointment(
        patient_name=data["patient_name"],
        patient_phone=data["patient_phone"],
        patient_tg_id=callback.from_user.id,
        patient_username=callback.from_user.username or "",
        doctor_id=data["doctor_id"],
        appointment_date=chosen_date,
        appointment_time=data["chosen_time"]
    )

    if not appointment:
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
            reply_markup=main_menu_keyboard()
        )
        return

    success_text = (
        f"🎉 *Navbat muvaffaqiyatli saqlandi!*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Navbat №: *{appointment.id}*\n"
        f"👨‍⚕️ Shifokor: *{appointment.doctor_name}*\n"
        f"🩺 Mutaxassis: *{appointment.doctor_specialty}*\n"
        f"📅 Sana: *{chosen_date.strftime('%d.%m.%Y')}*\n"
        f"🕐 Vaqt: *{data['chosen_time']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📍 *Manzil:* {CLINIC_ADDRESS}\n\n"
        f"🔔 Navbatdan 24 soat va 1 soat oldin eslatma yuboriladi.\n\n"
        f"_Navbatni bekor qilish uchun /my_appointments_"
    )

    await callback.message.edit_text(
        success_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()

    # Adminga xabar yuborish
    from aiogram import Bot
    bot = callback.bot
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 *Yangi navbat!*\n\n"
                f"👤 {appointment.patient_name} ({appointment.patient_phone})\n"
                f"👨‍⚕️ {appointment.doctor_name}\n"
                f"📅 {chosen_date.strftime('%d.%m.%Y')} soat {data['chosen_time']}",
                parse_mode="Markdown"
            )
        except:
            pass


# ===================== MENING NAVBATLARIM =====================

@router.callback_query(F.data == "my_appointments")
@router.message(F.text == "/my_appointments")
async def show_my_appointments(update, state: FSMContext):
    if isinstance(update, CallbackQuery):
        user_id = update.from_user.id
        edit = update.message.edit_text
    else:
        user_id = update.from_user.id
        edit = update.answer

    appointments = await get_patient_appointments(user_id)

    if not appointments:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="📋 Navbat olish", callback_data="book_appointment")
        builder.button(text="⬅️ Bosh menu", callback_data="main_menu")
        builder.adjust(1)

        await edit(
            "📭 Sizda hozircha faol navbatlar yo'q.\n\nYangi navbat olish uchun tugmani bosing:",
            reply_markup=builder.as_markup()
        )
        return

    await edit(
        f"🗓 *Sizning navbatlaringiz* ({len(appointments)} ta):\n\n"
        f"Navbat haqida batafsil ko'rish uchun tanlang:",
        reply_markup=my_appointments_keyboard(appointments),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("apt_"))
async def appointment_detail(callback: CallbackQuery):
    apt_id = int(callback.data.split("_")[1])

    from database.queries import AsyncSessionLocal, Appointment
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Appointment).where(Appointment.id == apt_id))
        apt = result.scalar_one_or_none()

    if not apt:
        await callback.answer("Navbat topilmadi!", show_alert=True)
        return

    apt_date = apt.appointment_datetime
    text = (
        f"📋 *Navbat №{apt.id}*\n\n"
        f"👨‍⚕️ *Shifokor:* {apt.doctor_name}\n"
        f"🩺 *Mutaxassis:* {apt.doctor_specialty}\n"
        f"📅 *Sana:* {apt_date.strftime('%d.%m.%Y')}\n"
        f"🕐 *Vaqt:* {apt_date.strftime('%H:%M')}\n"
        f"📍 *Manzil:* {CLINIC_ADDRESS}\n\n"
        f"_Navbatni bekor qilish uchun quyidagi tugmani bosing._"
    )

    await callback.message.edit_text(
        text,
        reply_markup=appointment_detail_keyboard(apt.id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("cancel_apt_"))
async def cancel_patient_appointment(callback: CallbackQuery):
    apt_id = int(callback.data.split("_")[2])

    success = await cancel_appointment(apt_id, reason="Mijoz tomonidan bekor qilindi")

    if success:
        await callback.message.edit_text(
            "✅ Navbatingiz bekor qilindi.\n\n"
            "Agar kerak bo'lsa, yangi navbat olishingiz mumkin.",
            reply_markup=main_menu_keyboard()
        )
        # Adminga xabar
        from aiogram import Bot
        for admin_id in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"❌ *Navbat bekor qilindi!*\n"
                    f"Navbat №{apt_id}\n"
                    f"Mijoz: {callback.from_user.full_name}",
                    parse_mode="Markdown"
                )
            except:
                pass
    else:
        await callback.answer("Navbatni bekor qilib bo'lmadi!", show_alert=True)
