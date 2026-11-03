
"""One parcel, with the only history the wall keeps — its events, in order."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import NoSuchParcel
from ..ids import parcel_internal, parcel_public
from ..models import Door, Event, Parcel
from ..schemas import EventOut, ParcelOut


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

    rows = session.scalars(
        select(Event)
        .where(Event.parcel_id == parcel.id)
        .order_by(Event.at, Event.id)
    )

    events = [
        EventOut(
            at=row.at,
            kind=row.kind,
            **json.loads(row.data),
        )
        for row in rows
    ]

    return ParcelOut(
        parcel_id=parcel_public(parcel.id),
        state=parcel.state,
        door=door.no,
        size_class=parcel.size_class,
        flat=parcel.flat,
        dropped_at=parcel.dropped_at,
        events=events,
    )
