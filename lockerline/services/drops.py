
"""A courier books a drop. Door choice, parcel and code are one transaction."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import Clock
from ..errors import NoDoorFree, NoSuchFlat
from ..models import Door, Parcel, Resident, Tower
from ..settings import Settings
from .codes import hash_code, issue_code
from .doors import free_sizes


def choose_door(
    session: Session,
    tower_id: int,
    size_class: str,
) -> Door | None:
    """Exact size only, lowest door number first — deterministic, so a test can name the door."""
    return session.scalar(
        select(Door)
        .where(
            Door.tower_id == tower_id,
            Door.size_class == size_class,
            Door.current_parcel_id.is_(None),
        )
        .order_by(Door.no)
        .limit(1)
    )


def unique_code(
    session: Session,
    tower_id: int,
    key: str,
) -> tuple[str, str]:
    """A fresh code whose hash no uncollected parcel in this tower already holds, so a code always names one door.
    (A collected parcel's code can come round again: it can never open anything a second time.)"""
    while True:
        code = issue_code()
        code_hash = hash_code(key, code)

        clash = session.scalar(
            select(Parcel.id)
            .where(
                Parcel.tower_id == tower_id,
                Parcel.code_hash == code_hash,
                Parcel.code_used_at.is_(None),
            )
            .limit(1)
        )

        if clash is None:
            return code, code_hash


def drop(
    session: Session,
    tower: Tower,
    size_class: str,
    flat: str,
    clock: Clock,
    settings: Settings,
) -> tuple[Parcel, Door, str]:
    resident = session.scalar(
        select(Resident).where(
            Resident.tower_id == tower.id,
            Resident.flat == flat,
        )
    )

    if resident is None:
        raise NoSuchFlat(
            f"Flat {flat!r} does not exist in tower {tower.code}"
        )

    door = choose_door(session, tower.id, size_class)

    if door is None:
        raise NoDoorFree(
            f"No free {size_class} door",
            free_sizes=free_sizes(session, tower.id),
        )

    now = clock.now()

    code, code_hash = unique_code(
        session,
        tower.id,
        settings.code_hash_key,
    )

    expires_at = now + timedelta(hours=settings.free_window_hours)

    parcel = Parcel(
        tower_id=tower.id,
        flat=flat,
        size_class=size_class,
        door_id=door.id,
        state="holding",
        dropped_at=now,
        code_hash=code_hash,
        code_expires_at=expires_at,
    )

    session.add(parcel)
    session.flush()

    door.current_parcel_id = parcel.id

    session.commit()

    return parcel, door, code
