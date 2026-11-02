
"""A presented code is checked; an unknown or expired code is refused."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clock import Clock, as_utc
from ..errors import CodeExpired, DomainError, NoSuchCode
from ..models import Door, Parcel
from ..settings import Settings
from .codes import hash_code, matches


def find_parcel(
    session: Session,
    code_hash: str,
) -> Parcel | None:
    """The parcel a code names (a drop never issues a code another parcel still holds unused)."""
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

    if parcel is None or not matches(key,code,parcel.code_hash):
        raise NoSuchCode("That code does not exist in this tower")

    now = clock.now()

    if now > as_utc(parcel.code_expires_at):
        # same status as no-such-code so a stranger cannot tell a wrong code from an old one; the type differs
        raise CodeExpired("That code's window has passed")

    # a valid code: opening the door, collecting the parcel and freeing the door is not built yet
    raise DomainError(
        "This code is valid, but opening the door is not available yet"
    )
