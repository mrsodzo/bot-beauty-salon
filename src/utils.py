from __future__ import annotations

from datetime import date, timedelta, time
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db import AsyncSessionLocal
from src.models import Slot, Master
from src.config import WORK_START, WORK_END, INTERVAL


def next_dates(n: int = 5) -> list[str]:
    today = date.today()
    return [(today + timedelta(days=i + 1)).strftime("%d.%m") for i in range(n)]


async def ensure_slots_for_date(target_date: date, master_id: int | None = None) -> None:
    async with AsyncSessionLocal() as session:
        stmt = select(Slot).where(Slot.date == target_date, Slot.is_booked == False)
        if master_id is not None:
            stmt = stmt.where(Slot.master_id == master_id)
        if (await session.execute(stmt)).first():
            return

        if master_id is not None:
            masters_to_gen = [master_id]
        else:
            masters_to_gen = list((await session.execute(select(Master.id))).scalars().all())

        for m_id in masters_to_gen:
            for hour in range(WORK_START, WORK_END):
                session.add(Slot(
                    master_id=m_id,
                    date=target_date,
                    time_start=time(hour, 0),
                    is_booked=False,
                ))
        await session.commit()


async def available_dates(n: int = 5, master_id: int | None = None) -> list[tuple[str, bool]]:
    result = []
    today = date.today()
    for i in range(n):
        d = today + timedelta(days=i + 1)
        await ensure_slots_for_date(d, master_id)
        slots = await free_slots_for(d, master_id)
        result.append((d.strftime("%d.%m"), len(slots) > 0))
    return result


async def free_slots_for(
    selected_date: date, master_id: int | None = None
) -> list[tuple[str, str, int, int]]:
    await ensure_slots_for_date(selected_date, master_id)
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Slot)
            .options(selectinload(Slot.master))
            .where(Slot.date == selected_date, Slot.is_booked == False)
        )
        result = (await session.execute(stmt)).scalars().all()
        seen: set[tuple] = set()
        slots: list[tuple[str, str, int, int]] = []
        for slot in result:
            if master_id is not None and slot.master_id != master_id:
                continue
            key = (slot.time_start, slot.master_id)
            if key in seen:
                continue
            seen.add(key)
            slots.append((
                slot.time_start.strftime("%H:%M"),
                slot.master.name,
                slot.master_id,
                slot.id,
            ))
        return sorted(slots, key=lambda x: x[0])
