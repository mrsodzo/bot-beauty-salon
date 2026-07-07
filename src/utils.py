from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db import AsyncSessionLocal
from src.models import Slot
from src.config import WORK_START, WORK_END, INTERVAL


def next_dates(n: int = 5) -> list[str]:
    today = date.today()
    return [(today + timedelta(days=i + 1)).strftime("%d.%m") for i in range(n)]


async def available_dates(n: int = 5, master_id: int | None = None) -> list[tuple[str, bool]]:
    result = []
    today = date.today()
    for i in range(n):
        d = today + timedelta(days=i + 1)
        slots = await free_slots_for(d, master_id)
        result.append((d.strftime("%d.%m"), len(slots) > 0))
    return result


async def free_slots_for(
    selected_date: date, master_id: int | None = None
) -> list[tuple[str, str, int, int]]:
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
