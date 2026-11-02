
"""A six-digit code, stored only as a hash, expiring FREE_WINDOW_HOURS after the drop by the injected clock."""

from datetime import timedelta
from unittest.mock import patch

from sqlalchemy import select

from lockerline.models import Parcel
from lockerline.services.codes import hash_code
from tests.conftest import T0, drop, make_settings


def test_code_is_six_digits_and_expires_after_the_window(client):
    body = drop(client)

    assert (
        len(body["code"]) == 6
        and body["code"].isdigit()
    )

    assert body["dropped_at"] == "2026-09-25T13:10:00Z"

    assert body["expires_at"] == (
        T0 + timedelta(hours=48)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_only_a_hash_is_stored(client, db):
    body = drop(client)

    with db() as s:
        parcel = s.scalar(select(Parcel))

        assert parcel.code_hash != body["code"]

        assert parcel.code_hash == hash_code("test-key", body["code"])

        for column in Parcel.__table__.columns:
            assert str(getattr(parcel, column.name)) != body["code"]


def test_two_drops_get_different_codes(client):
    assert drop(client)["code"] != drop(client)["code"]


def test_window_comes_from_settings(tmp_path, clock):
    from fastapi.testclient import TestClient

    from lockerline.app import create_app
    from lockerline.clock import get_clock

    app = create_app(make_settings(tmp_path, free_window_hours=24))
    app.dependency_overrides[get_clock] = lambda: clock

    with TestClient(app) as c:
        assert drop(c)["expires_at"] == (
            T0 + timedelta(hours=24)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")


def test_codes_are_not_derivable_from_the_parcel_id(tmp_path, clock):
    """Two fresh databases, the same first parcel id (P001), the same clock: the codes still differ, so nothing
    about the parcel id (or the time) produces the code."""

    from fastapi.testclient import TestClient

    from lockerline.app import create_app
    from lockerline.clock import get_clock

    codes = []

    for name in ("one", "two"):
        folder = tmp_path / name
        folder.mkdir()

        app = create_app(make_settings(folder))
        app.dependency_overrides[get_clock] = lambda: clock

        with TestClient(app) as c:
            body = drop(c)

        assert (
            body["parcel_id"] == "P001"
            and body["door"] == "D21"
        )

        codes.append(body["code"])

    assert codes[0] != codes[1]

    
def test_a_code_an_uncollected_parcel_holds_is_never_issued_again(client, db):
    """The collision bug: the random source repeats a code while the first parcel is still in its door.
    The drop draws again, so every uncollected parcel's code names exactly one door."""

    with patch(
        "lockerline.services.drops.issue_code",
        side_effect=["111111", "111111", "222222"],
    ):
        first, second = drop(client), drop(client)

    assert (
        first["code"] == "111111"
        and second["code"] == "222222"
    )

    with db() as s:
        hashes = list(s.scalars(select(Parcel.code_hash)))

    assert len(set(hashes)) == 2

