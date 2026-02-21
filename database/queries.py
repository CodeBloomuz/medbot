from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, date
from typing import List, Optional

from database.db import AsyncSessionLocal, Doctor, Appointment, BlockedSlot
from config import WORK_START, WORK_END, SLOT_DURATION


async def get_all_doctors() -> List[Doctor]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.is_active == True).order_by(Doctor.id)
        )
        return result.scalars().all()


async def get_doctor_by_id(doctor_id: int) -> Optional[Doctor]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
        return result.scalar_one_or_none()


async def get_available_dates(doctor_id: int) -> List[date]:
    """Keyingi 14 kunda shifokor ishlaydi qanday kunlarni qaytaradi"""
    doctor = await get_doctor_by_id(doctor_id)
    if not doctor:
        return []

    work_days = [int(d) for d in doctor.work_days.split(",")]
    available_dates = []

    for i in range(1, 15):  # Ertadan boshlab 14 kun
        check_date = datetime.now().date() + timedelta(days=i)
        # isoweekday(): 1=Dushanba, 7=Yakshanba
        if check_date.isoweekday() in work_days:
            available_dates.append(check_date)

    return available_dates[:7]  # Max 7 kun ko'rsat


async def get_available_slots(doctor_id: int, check_date: date) -> List[str]:
    """Berilgan kunda bo'sh vaqt slotlarini qaytaradi"""
    doctor = await get_doctor_by_id(doctor_id)
    if not doctor:
        return []

    # Barcha vaqt slotlarini yaratish
    work_start = datetime.strptime(doctor.work_start, "%H:%M")
    work_end = datetime.strptime(doctor.work_end, "%H:%M")
    duration = timedelta(minutes=doctor.slot_duration)

    all_slots = []
    current = work_start
    while current + duration <= work_end:
        all_slots.append(current.strftime("%H:%M"))
        current += duration

    # Band bo'lgan slotlarni olish
    async with AsyncSessionLocal() as session:
        date_start = datetime.combine(check_date, datetime.min.time())
        date_end = datetime.combine(check_date, datetime.max.time())

        result = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_datetime >= date_start,
                    Appointment.appointment_datetime <= date_end,
                    Appointment.status == "active"
                )
            )
        )
        booked = result.scalars().all()
        booked_times = {apt.appointment_datetime.strftime("%H:%M") for apt in booked}

        # Bloklangan slotlarni tekshirish
        blocked_result = await session.execute(
            select(BlockedSlot).where(
                and_(
                    BlockedSlot.doctor_id == doctor_id,
                    BlockedSlot.blocked_date == check_date.strftime("%Y-%m-%d")
                )
            )
        )
        blocked = blocked_result.scalars().all()

        # Butun kun bloklangan bo'lsa
        if any(b.blocked_time is None for b in blocked):
            return []

        blocked_times = {b.blocked_time for b in blocked if b.blocked_time}

    # Hozirgi vaqtdan o'tgan slotlarni o'chirish (bugun uchun)
    now = datetime.now()
    if check_date == now.date():
        all_slots = [s for s in all_slots
                     if datetime.strptime(s, "%H:%M").replace(
                         year=now.year, month=now.month, day=now.day) > now]

    return [s for s in all_slots if s not in booked_times and s not in blocked_times]


async def create_appointment(
    patient_name: str,
    patient_phone: str,
    patient_tg_id: int,
    patient_username: str,
    doctor_id: int,
    appointment_date: date,
    appointment_time: str
) -> Optional[Appointment]:
    doctor = await get_doctor_by_id(doctor_id)
    if not doctor:
        return None

    apt_datetime = datetime.combine(
        appointment_date,
        datetime.strptime(appointment_time, "%H:%M").time()
    )

    async with AsyncSessionLocal() as session:
        appointment = Appointment(
            patient_name=patient_name,
            patient_phone=patient_phone,
            patient_tg_id=patient_tg_id,
            patient_username=patient_username,
            doctor_id=doctor_id,
            doctor_name=doctor.name,
            doctor_specialty=doctor.specialty,
            appointment_datetime=apt_datetime,
            status="active"
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return appointment


async def cancel_appointment(appointment_id: int, reason: str = None) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        apt = result.scalar_one_or_none()
        if apt and apt.status == "active":
            apt.status = "cancelled"
            apt.cancel_reason = reason
            await session.commit()
            return True
        return False


async def get_patient_appointments(tg_id: int) -> List[Appointment]:
    """Mijozning kelgusidagi navbatlarini olish"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.patient_tg_id == tg_id,
                    Appointment.status == "active",
                    Appointment.appointment_datetime >= datetime.now()
                )
            ).order_by(Appointment.appointment_datetime)
        )
        return result.scalars().all()


async def get_todays_appointments() -> List[Appointment]:
    """Bugungi barcha navbatlar"""
    async with AsyncSessionLocal() as session:
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        today_end = datetime.combine(datetime.now().date(), datetime.max.time())

        result = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.appointment_datetime >= today_start,
                    Appointment.appointment_datetime <= today_end,
                    Appointment.status == "active"
                )
            ).order_by(Appointment.appointment_datetime)
        )
        return result.scalars().all()


async def get_appointments_for_reminder(target_datetime: datetime, window_minutes: int = 15) -> List[Appointment]:
    """Eslatma yuborish kerak bo'lgan navbatlarni olish"""
    async with AsyncSessionLocal() as session:
        time_from = target_datetime - timedelta(minutes=window_minutes)
        time_to = target_datetime + timedelta(minutes=window_minutes)

        result = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.appointment_datetime >= time_from,
                    Appointment.appointment_datetime <= time_to,
                    Appointment.status == "active"
                )
            )
        )
        return result.scalars().all()


async def mark_reminder_sent(appointment_id: int, reminder_type: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        apt = result.scalar_one_or_none()
        if apt:
            if reminder_type == "24h":
                apt.reminder_24h_sent = True
            elif reminder_type == "1h":
                apt.reminder_1h_sent = True
            await session.commit()


async def get_statistics() -> dict:
    """Admin uchun statistika"""
    async with AsyncSessionLocal() as session:
        # Jami navbatlar
        total = await session.execute(select(func.count(Appointment.id)))

        # Bugungi navbatlar
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        today_end = datetime.combine(datetime.now().date(), datetime.max.time())
        today = await session.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.appointment_datetime >= today_start,
                    Appointment.appointment_datetime <= today_end
                )
            )
        )

        # Bekor qilinganlar (bu oy)
        month_start = datetime.now().replace(day=1, hour=0, minute=0)
        cancelled = await session.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.status == "cancelled",
                    Appointment.created_at >= month_start
                )
            )
        )

        # Faol navbatlar
        active = await session.execute(
            select(func.count(Appointment.id)).where(
                and_(
                    Appointment.status == "active",
                    Appointment.appointment_datetime >= datetime.now()
                )
            )
        )

        return {
            "total": total.scalar(),
            "today": today.scalar(),
            "cancelled_month": cancelled.scalar(),
            "upcoming": active.scalar()
        }


async def add_doctor(name: str, specialty: str, emoji: str = "👨‍⚕️") -> Doctor:
    async with AsyncSessionLocal() as session:
        doctor = Doctor(name=name, specialty=specialty, emoji=emoji)
        session.add(doctor)
        await session.commit()
        await session.refresh(doctor)
        return doctor


async def toggle_doctor(doctor_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar_one_or_none()
        if doctor:
            doctor.is_active = not doctor.is_active
            await session.commit()
            return doctor.is_active
        return False
