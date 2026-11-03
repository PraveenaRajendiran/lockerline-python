
"""One parametrised table of every refusal, run with the clock overridden — then the window changes
from 48 to 24 hours and exactly the rows tagged `window` move.
"""

import csv
import json
import re

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from lockerline.app import create_app
from lockerline.clock import FixedClock, get_clock
from tests.conftest import T0, fill, make_settings


ROWS = list(
    csv.DictReader(
        (Path(__file__).parent / "rules.csv").open(encoding="utf-8")
    )
)


def run_case(client, clock, row):
    last_code = None

    for step in filter(None, row["setup"].split(";")):
        verb, *args = step.split()

        if verb == "fill":
            fill(client, args[0])

        elif verb == "drop":
            response = client.post(
                "/drops",
                json={
                    "size_class": args[0] if args else "M",
                    "flat": args[1] if len(args) > 1 else "302",
                },
            )
            assert response.status_code == 201, response.text
            last_code = response.json()["code"]

        elif verb == "pickup":
            response = client.post(
                "/pickups",
                json={"code": last_code},
            )
            assert response.status_code == 200, response.text

        elif verb == "advance":
            clock.advance(hours=int(args[0]))

    verb, *args = row["action"].split()

    if verb == "drop":
        return client.post(
            "/drops",
            json={
                "size_class": args[0],
                "flat": args[1],
            },
        )

    return client.post(
        "/pickups",
        json={"code": args[0] if args else last_code},
    )


@pytest.mark.parametrize(
    "row",
    ROWS,
    ids=[row["case"] for row in ROWS],
)
def test_rule_table(tmp_path, row):
    results = {}

    for window in [48, 24]:
        window_path = tmp_path / f"window-{window}"
        window_path.mkdir()

        clock = FixedClock(T0)

        app = create_app(
            make_settings(window_path, free_window_hours=window)
        )
        app.dependency_overrides[get_clock] = lambda: clock

        with TestClient(app) as client:
            response = run_case(client, clock, row)

            results[window] = (
                response.status_code,
                response.json(),
            )

    for window in [48, 24]:
        status_code, body = results[window]

        assert status_code == int(row[f"status_{window}"]), (
            row["case"],
            window,
            body,
        )

        expected_type = row[f"type_{window}"]

        if expected_type:
            assert body["type"] == expected_type

def test_only_window_rows_move_when_the_window_changes():
    moved = {
        row["case"]
        for row in ROWS
        if row["status_48"] != row["status_24"]
    }

    assert moved and all(
        row["tag"] == "window"
        for row in ROWS
        if row["case"] in moved
    )


def test_every_refusal_type_has_a_row():
    types = {
        row["type_48"] for row in ROWS
    } | {
        row["type_24"] for row in ROWS
    }

    assert types >= {
        "/errors/no-door-free",
        "/errors/no-such-flat",
        "/errors/validation",
        "/errors/code-used",
        "/errors/no-such-code",
        "/errors/code-expired",
    }


def test_settings_endpoint_shows_the_live_window(tmp_path, clock):
    app = create_app(make_settings(tmp_path, free_window_hours=24))

    with TestClient(app) as client:
        assert client.get("/settings").json() == {
            "free_window_hours": 24,
            "sizes": ["S", "M", "L"],
        }


def test_the_rule_book_shows_the_rows_the_tests_run():
    """The Rule book screen renders a copy of tests/rules.csv; the copy must equal the
    file: same cases, tags, setup, action and expected status/type at both windows, in the same order.
    """

    source = (Path(__file__).resolve().parent.parent / "lockerline" / "static" / "app.js").read_text(encoding="utf-8")

    block = re.search(
        r"var RULES = (\[.*?\n  \]);",
        source,
        re.DOTALL,
    )

    assert block, "app.js declares var RULES = [...]"

    shown = json.loads(block.group(1))

    columns = [
        "case",
        "tag",
        "setup",
        "action",
        "status_48",
        "type_48",
        "status_24",
        "type_24",
    ]

    assert shown == [
        [row[column] for column in columns]
        for row in ROWS
    ]
