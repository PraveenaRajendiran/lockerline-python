
"""One parcel."""

from sqlalchemy.orm import Session

from ..errors import NoSuchParcel
from ..ids import parcel_internal, parcel_public
from ..models import Door, Parcel
from ..schemas import ParcelOut


def get_parcel(
    session: Session,
    public_id: str,
) -> ParcelOut:
    internal = parcel_internal(public_id)

    parcel = (
        session.get(Parcel, internal)
        if internal is not None
        else None
    )

    if parcel is None:
        raise NoSuchParcel(
            f"There is no parcel {public_id!r}"
        )

    door = session.get(Door, parcel.door_id)

    return ParcelOut(
        parcel_id=parcel_public(parcel.id),
        state=parcel.state,
        door=door.no,
        size_class=parcel.size_class,
        flat=parcel.flat,
        dropped_at=parcel.dropped_at,
    )
