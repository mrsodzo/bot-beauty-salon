from __future__ import annotations

import asyncio
from datetime import date, timedelta, time as dtime

from src.config import SALON_NAME
from src.db import engine, AsyncSessionLocal
from src.models import Base, Master, Service, Slot
from sqlalchemy import select, func


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(func.count(Master.id)))).scalar_one()
        if existing > 0:
            print("Demo data already seeded.")
            return

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
            session.add(Master(**m))

        for name, price, duration, master_id in services:
            session.add(
                Service(name=name, price=price, duration_min=duration, master_id=master_id)
            )

        for master_id in range(1, 4):
            for future in range(1, 6):
                slot_date = date.today() + timedelta(days=future)
                for hour in range(10, 19):
                    session.add(
                        Slot(
                            master_id=master_id,
                            date=slot_date,
                            time_start=dtime(hour, 0),
                            is_booked=False,
                        )
                    )

        await session.commit()

    print("Demo data seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
