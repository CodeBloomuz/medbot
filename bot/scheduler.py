from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def send_reminders(bot: Bot):
    """Har 10 daqiqada ishga tushadi — eslatmalarni yuboradi"""
    try:
        from database.queries import get_appointments_for_reminder, mark_reminder_sent
        from database.db import AsyncSessionLocal, Appointment
        from sqlalchemy import select, and_
        now = datetime.now()

        async with AsyncSessionLocal() as session:
            # 24 soat oldin eslatma
            target_24h = now + timedelta(hours=24)
            result_24h = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.appointment_datetime >= target_24h - timedelta(minutes=10),
                        Appointment.appointment_datetime <= target_24h + timedelta(minutes=10),
                        Appointment.status == "active",
                        Appointment.reminder_24h_sent == False
                    )
                )
            )
            apts_24h = result_24h.scalars().all()

            for apt in apts_24h:
                try:
                    apt_time = apt.appointment_datetime.strftime("%H:%M")
                    apt_date = apt.appointment_datetime.strftime("%d.%m.%Y")

                    await bot.send_message(
                        apt.patient_tg_id,
                        f"🔔 *Navbat eslatmasi!*\n\n"
                        f"Ertaga navbatingiz bor:\n\n"
                        f"👨‍⚕️ *{apt.doctor_name}*\n"
                        f"🩺 {apt.doctor_specialty}\n"
                        f"📅 {apt_date} soat {apt_time}\n\n"
                        f"Kela olmasangiz navbatni bekor qiling:\n/my_appointments",
                        parse_mode="Markdown"
                    )
                    apt.reminder_24h_sent = True
                    logger.info(f"24h reminder sent for appointment {apt.id}")
                except Exception as e:
                    logger.error(f"Failed to send 24h reminder for apt {apt.id}: {e}")

            # 1 soat oldin eslatma
            target_1h = now + timedelta(hours=1)
            result_1h = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.appointment_datetime >= target_1h - timedelta(minutes=10),
                        Appointment.appointment_datetime <= target_1h + timedelta(minutes=10),
                        Appointment.status == "active",
                        Appointment.reminder_1h_sent == False
                    )
                )
            )
            apts_1h = result_1h.scalars().all()

            for apt in apts_1h:
                try:
                    apt_time = apt.appointment_datetime.strftime("%H:%M")

                    await bot.send_message(
                        apt.patient_tg_id,
                        f"⏰ *1 soat qoldi!*\n\n"
                        f"Bugun soat *{apt_time}* da\n"
                        f"*{apt.doctor_name}* qabuliga yozilgansiz.\n\n"
                        f"O'z vaqtida keling! 🏥",
                        parse_mode="Markdown"
                    )
                    apt.reminder_1h_sent = True
                    logger.info(f"1h reminder sent for appointment {apt.id}")
                except Exception as e:
                    logger.error(f"Failed to send 1h reminder for apt {apt.id}: {e}")

            await session.commit()

    except Exception as e:
        logger.error(f"Scheduler error: {e}")


async def mark_done_appointments():
    """O'tib ketgan navbatlarni 'done' qilish"""
    try:
        from database.db import AsyncSessionLocal, Appointment
        from sqlalchemy import select, and_

        async with AsyncSessionLocal() as session:
            past_time = datetime.now() - timedelta(hours=1)
            result = await session.execute(
                select(Appointment).where(
                    and_(
                        Appointment.appointment_datetime <= past_time,
                        Appointment.status == "active"
                    )
                )
            )
            past_apts = result.scalars().all()

            for apt in past_apts:
                apt.status = "done"

            if past_apts:
                await session.commit()
                logger.info(f"Marked {len(past_apts)} appointments as done")

    except Exception as e:
        logger.error(f"Mark done error: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Eslatmalarni har 10 daqiqada tekshirish
    scheduler.add_job(
        send_reminders,
        "interval",
        minutes=10,
        args=[bot],
        id="reminders"
    )

    # O'tgan navbatlarni har soatda yangilash
    scheduler.add_job(
        mark_done_appointments,
        "interval",
        hours=1,
        id="mark_done"
    )

    scheduler.start()
    logger.info("✅ Scheduler started (Asia/Tashkent timezone)")
    return scheduler
