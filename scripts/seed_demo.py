from __future__ import annotations

import asyncio
import logging
import random
from datetime import date, timedelta, time as dtime

from src.config import SALON_NAME, WORK_START, WORK_END
from src.db import engine, AsyncSessionLocal
from src.models import Base, Master, Service, Slot
from sqlalchemy import select, func, delete

logger = logging.getLogger(__name__)


async def seed() -> None:
    logger.info("Создание базы данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных создана.")

    async with AsyncSessionLocal() as session:
        masters = [
            {"name": "Алексей", "description": "Стрижки и укладки", "is_active": True},
            {"name": "Максим", "description": "Окрашивание и уход", "is_active": True},
            {"name": "Лев", "description": "Барбер и маникюр", "is_active": True},
        ]

        services = [
            ("Стрижка классическая", 1500, 60, 1),
            ("Укладка", 1200, 45, 1),
            ("Детская стрижка", 1000, 45, 1),
            ("Окрашивание", 3000, 120, 2),
            ("Уход за бородой", 800, 30, 2),
            ("Барбер", 2000, 60, 3),
            ("Маникюр классический", 1800, 60, 3),
            ("Маникюр с покрытием", 2500, 90, 3),
        ]

        for m in masters:
            stmt = select(Master).where(Master.name == m["name"])
            if not (await session.execute(stmt)).first():
                session.add(Master(**m))

        for name, price, duration, master_id in services:
            stmt = select(Service).where(Service.name == name)
            if not (await session.execute(stmt)).first():
                session.add(Service(name=name, price=price, duration_min=duration, master_id=master_id))

        await session.commit()

        master_ids = [m.id for m in (await session.execute(select(Master))).scalars().all()]
        today = date.today()

        await session.execute(
            delete(Slot).where(Slot.is_booked == False, Slot.date >= today)
        )
        await session.commit()

        created = []
        for master_id in master_ids:
            for future in range(1, 6):
                slot_date = today + timedelta(days=future)
                available_hours = list(range(WORK_START, WORK_END))
                random.shuffle(available_hours)
                for hour in available_hours[:random.randint(1, 3)]:
                    session.add(Slot(
                        master_id=master_id,
                        date=slot_date,
                        time_start=dtime(hour, 0),
                        is_booked=False,
                    ))
                    created.append((master_id, slot_date, dtime(hour, 0)))

        await session.commit()

        for master_id, slot_date, time_start in created:
            master_name = {1: "Алексей", 2: "Максим", 3: "Лев"}.get(master_id, str(master_id))
            logger.info("Создан слот: %s | %s | %s", master_name, slot_date.strftime("%d.%m"), time_start.strftime("%H:%M"))

        logger.info("Всего создано слотов: %s", len(created))

    logger.info("Demo data seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
