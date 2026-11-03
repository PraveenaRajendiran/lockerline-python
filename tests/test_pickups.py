
"""A valid code opens the door once, frees it and stamps dwell — atomically."""

from sqlalchemy import func, select, text

from lockerline.models import Door, Event, Parcel
from tests.conftest import drop


def test_pickup_frees_door_and_stamps_dwell(client, clock, db):
    body = drop(client)

    clock.advance(days=1, hours=20, minutes=2)  # 158520 s

    r = client.post(
        "/pickups",
        json={"code": body["code"]},
    )

    assert r.status_code == 200

    out = r.json()

    assert (
        out["parcel_id"] == body["parcel_id"]
        and out["door"] == body["door"]
    )

    assert (
        out["dwell_seconds"] == 158520
        and out["opened_at"] == "2026-09-27T09:12:00Z"
    )

    with db() as s:
        parcel = s.scalar(select(Parcel))

        assert (
            parcel.state == "collected"
            and parcel.dwell_seconds == 158520
            and parcel.code_used_at is not None
        )

        door = s.scalar(select(Door).where(Door.no == body["door"]))
        assert door.current_parcel_id is None

    assert client.get("/towers/A/doors").json()["free"] == 48


def test_second_pickup_is_refused_and_changes_nothing(client, clock, db):
    body = drop(client)

    assert client.post(
        "/pickups",
        json={"code": body["code"]},
    ).status_code == 200

    def snapshot():
        with db() as s:
            p = s.scalar(select(Parcel))
            door = s.scalar(
                select(Door).where(Door.no == body["door"])
            )
            events = s.scalar(
                select(func.count()).select_from(Event)
            )

            return (
                p.state,
                p.collected_at,
                p.code_used_at,
                p.dwell_seconds,
                door.current_parcel_id,
                events,
            )

    before = snapshot()
    clock.advance(minutes=1)

    r = client.post(
        "/pickups",
        json={"code": body["code"]},
    )

    assert (
        r.status_code == 409
        and r.json()["type"] == "/errors/code-used"
    )

    assert snapshot() == before                 # parcel, door and event count unchanged
    assert before[4] is None and before[5] == 3


def test_failure_after_parcel_update_rolls_back(client, db):
    body = drop(client)

    with db() as s:  # the database refuses the pickup's second write - the door letting the parcel go
        s.execute(
            text(
                "CREATE TRIGGER fail_release BEFORE UPDATE ON doors WHEN NEW.current_parcel_id IS NULL "
                "BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
            )
        )
        s.commit()

    assert client.post(
        "/pickups",
        json={"code": body["code"]},
    ).status_code == 500

    with db() as s:
        parcel = s.scalar(select(Parcel))

        assert (
            parcel.state == "holding"
            and parcel.code_used_at is None
        )

        door = s.scalar(select(Door).where(Door.no == body["door"]))
        assert door.current_parcel_id == parcel.id


def test_malformed_code_is_422(client):
    r = client.post(
        "/pickups",
        json={"code": "12ab"},
    )

    assert (
        r.status_code == 422
        and r.json()["errors"][0]["field"] == "code"
    )
