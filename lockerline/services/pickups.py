
"""A code opens its door once. Accept, collect, free the door and stamp dwell — one transaction."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import Clock, as_utc
from ..errors import CodeExpired, CodeUsed, NoSuchCode
from ..models import Door, Parcel
from ..settings import Settings
from .codes import hash_code, matches


def find_parcel(
    session: Session,
    code_hash: str,
) -> Parcel | None:
    """The parcel a code names. A drop never issues a code an uncollected parcel already holds, but a collected
    parcel's code can come round again — so the uncollected parcel wins; only if there is none is it a used code."""
    return session.scalar(
        select(Parcel)
        .where(Parcel.code_hash == code_hash)
        .order_by(
            Parcel.code_used_at.is_not(None),
            Parcel.id.desc(),
        )
        .limit(1)
    )


def pickup(
    session: Session,
    code: str,
    clock: Clock,
    settings: Settings,
) -> tuple[Parcel, Door]:
    key = settings.code_hash_key

    parcel = find_parcel(
        session,
        hash_code(key, code),
    )

    if parcel is None or not matches(key, code, parcel.code_hash):
        raise NoSuchCode("That code does not exist in this tower")

    if parcel.code_used_at is not None:
        raise CodeUsed("That code has already opened its door")

    now = clock.now()

    if now > as_utc(parcel.code_expires_at):
        # Same status as no-such-code so a stranger cannot tell a wrong code from an old one;
        # the type differs.
        raise CodeExpired("That code's window has passed")

    door = session.get(Door, parcel.door_id)

    dwell = int(
        (now - as_utc(parcel.dropped_at)).total_seconds()
    )

    parcel.state = "collected"
    parcel.collected_at = now
    parcel.dwell_seconds = dwell
    parcel.code_used_at = now

    door.current_parcel_id = None

    session.commit()

    return parcel, door
