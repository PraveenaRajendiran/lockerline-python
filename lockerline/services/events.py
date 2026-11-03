"""Append one event row inside the caller's transaction. Never the code, never a name.

The row is written with a Core INSERT and only its new id comes back, so no ORM object for an event is ever held in
a session: there is no path in the code that could change or delete one (the database triggers refuse it as well).
"""

import json
import logging
from datetime import datetime

from sqlalchemy import insert
from sqlalchemy.orm import Session

from ..ids import parcel_public
from ..models import Event

log = logging.getLogger("lockerline.events")


def record(
    session: Session,
    tower_id: int,
    parcel_id: int,
    kind: str,
    at: datetime,
    data: dict | None = None,
) -> int:
    facts = data or {}

    event_id = session.execute(
        insert(Event).values(
            tower_id=tower_id,
            parcel_id=parcel_id,
            kind=kind,
            at=at,
            data=json.dumps(facts),
        ).returning(Event.id)
    ).scalar_one()

    # Public ids only: the parcel as P001, the facts the event carries (a door number, an expiry, a dwell).
    log.info("event kind=%s parcel_id=%s %s", kind, parcel_public(parcel_id), " ".join(f"{k}={v}" for k, v in facts.items()))

    return event_id
