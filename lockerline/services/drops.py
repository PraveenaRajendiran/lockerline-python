
"""A courier books a drop. Door choice and parcel are one transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import Clock
from ..errors import NoDoorFree, NoSuchFlat
from ..models import Door, Parcel, Resident, Tower
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


def drop(
    session: Session,
    tower: Tower,
    size_class: str,
    flat: str,
    clock: Clock,
) -> tuple[Parcel, Door]:
    resident = session.scalar(select(Resident).where(Resident.tower_id == tower.id, Resident.flat == flat))

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

    parcel = Parcel(
        tower_id=tower.id,
        flat=flat,
        size_class=size_class,
        door_id=door.id,
        state="holding",
        dropped_at=now,
    )

    session.add(parcel)
    session.flush()

    door.current_parcel_id = parcel.id

    session.commit()

    return parcel, door
