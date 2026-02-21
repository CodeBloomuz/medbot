from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime

from config import DATABASE_URL

# PostgreSQL URL ni async formatga o'tkazish
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL_ASYNC = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL_ASYNC = DATABASE_URL

engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)          # "Karimov Jasur Aliyevich"
    specialty = Column(String(100), nullable=False)     # "Kardiolog"
    emoji = Column(String(10), default="👨‍⚕️")          # Ikonka
    work_days = Column(String(20), default="1,2,3,4,5") # 1=Dush, 7=Yak
    work_start = Column(String(5), default="09:00")
    work_end = Column(String(5), default="18:00")
    slot_duration = Column(Integer, default=30)         # daqiqa
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_name = Column(String(100), nullable=False)
    patient_phone = Column(String(20), nullable=False)
    patient_tg_id = Column(Integer, nullable=False)
    patient_username = Column(String(100), nullable=True)
    doctor_id = Column(Integer, nullable=False)
    doctor_name = Column(String(100), nullable=False)
    doctor_specialty = Column(String(100), nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")  # active, cancelled, done
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_1h_sent = Column(Boolean, default=False)
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class BlockedSlot(Base):
    """Shifokor dam olishi yoki ta'til uchun bloklangan vaqtlar"""
    __tablename__ = "blocked_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, nullable=False)
    blocked_date = Column(String(10), nullable=False)  # "2024-12-25"
    blocked_time = Column(String(5), nullable=True)    # None = butun kun
    reason = Column(String(200), nullable=True)


async def init_db():
    """Barcha jadvallarni yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Default shifokorlarni qo'shish (agar bo'sh bo'lsa)
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Doctor))
        if not result.scalars().first():
            default_doctors = [
                Doctor(name="Karimov Jasur Aliyevich", specialty="Terapevt", emoji="👨‍⚕️"),
                Doctor(name="Yusupova Malika Xasan qizi", specialty="Kardiolog", emoji="❤️"),
                Doctor(name="Rahimov Sherzod Baxtiyorovich", specialty="Nevropatolog", emoji="🧠"),
                Doctor(name="Toshmatova Nilufar Saidovna", specialty="Stomatolog", emoji="🦷"),
            ]
            session.add_all(default_doctors)
            await session.commit()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
