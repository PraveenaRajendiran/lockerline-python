# LockerLine

A bank of 48 parcel lockers for one apartment tower. Couriers drop, residents collect with a six-digit code that expires. This folder is the project so far.

## What is here

| Part | What it does |
|---|---|
| The wall | 48 doors and the residents seeded once at start-up; `GET /towers/{tower}/doors` with size/state filters; door state **derived** from the parcel in it |
| Drops | `POST /drops` — the lowest free door of the exact size, one transaction; 400 vs 422 vs 409; `GET /parcels/{id}` |
| Codes | A one-time six-digit code, stored only as a keyed hash, expiring `FREE_WINDOW_HOURS` after the drop by an injected clock |
| Refusals | Three refusals with their own types (`no-door-free`, `code-used`, `no-such-code`/`code-expired`) raised from the service, mapped once |
| Pickups | `POST /pickups` — opens the door once, frees it and stamps dwell time, atomically |
| Events | An append-only event log written in the same transaction; the database refuses UPDATE/DELETE on it |
| The API | Routers per resource, one error handler, `/docs` listing every refusal with an example |
| Rules | A parametrised rule table (`tests/rules.csv`) run at 48 h and 24 h — only the `window` rows move; `GET /settings` |
| The image | A Dockerfile, `HOST=0.0.0.0`, port 8080, `GET /healthz` that reaches the database |

## Run it locally

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt     # Windows; use .venv/bin on Linux/macOS
python -m uvicorn lockerline.app:app --host 127.0.0.1 --port 8080
```

Open <http://localhost:8080/> for the wall and <http://localhost:8080/docs> for the API. Settings come from the environment or a `.env` file; nothing is hard-coded.

Run the tests: `python -m pytest tests`. The grading suite: `python -m pytest sandbox`.

## Run it in a container

The two commands:

```bash
docker build -t lockerline .
docker run -p 8080:8080 lockerline
```

The image's command is `uvicorn lockerline.app:app --host 0.0.0.0 --port 8080`, written so the shell fills in `HOST` and `PORT` from the environment:

```dockerfile
CMD ["sh", "-c", "exec uvicorn lockerline.app:app --host \"$HOST\" --port \"$PORT\""]
```

## Conventions

- Every error is `application/problem+json`: `{type, title, status, detail}` plus the fields named for that refusal.
- Ids on the wire are opaque strings (`P001`, `D21`); database integers never leave the app.
- The pickup code is hashed with keyed SHA-256 (HMAC with `CODE_HASH_KEY`), not bcrypt. A code has only a million values, so an unkeyed hash of a leaked table could be reversed in seconds. The key, which is not in the database, makes the stored hash useless without it, and a keyed hash can still be looked up by equality. The plain code appears in the drop response and nowhere else: not in the database, not in an event.
- The clock and the database session are dependencies, so every time-based rule is tested against a fixed clock.

## Verified on this build

Run on **[actual date]** with Docker **[actual version]** on **[actual system]**. The image was tagged `lockerline` and the host port was `8080`.

| Check | Result |
|---|---|
| `docker build` | succeeds; image **[actual size] MB** |
| `GET /healthz` from the host | `{"status":"ok"}` 200 |
| `GET /towers/A/doors` from the host | 48 doors, `free` 48 |
| The same two from another container (`docker run --rm --entrypoint python lockerline -c "…urlopen('http://host.docker.internal:8080/…')"`)| `b'{"status":"ok"}'` and `48 48` |
| `pip freeze` in the image | equals `requirements.lock`: 17 packages, ignoring pip/setuptools/wheel |
| `find /app -name __pycache__ -o -name '*.db' -o -name sandbox -o -name tests` in the image | prints nothing |

<!-- learntube:start -->
---

[![tests](https://github.com/PraveenaRajendiran/lockerline-python/actions/workflows/tests.yml/badge.svg)](https://github.com/PraveenaRajendiran/lockerline-python/actions/workflows/tests.yml)

### Progress

- [x] Ticket 1 · Forty-eight doors, and a wall you can look at
- [x] Ticket 2 · A courier asks for a door
- [x] Ticket 3 · The code that dies at midnight
- [x] Ticket 4 · Three ways to say no
- [x] Ticket 5 · The door opens, and the clock stops
- [x] Ticket 6 · A notebook nobody can rewrite
- [x] Ticket 7 · One file becomes an app
- [x] Ticket 8 · The rule table, and then the rule changes
- [x] Ticket 9 · It runs on a machine that isn't yours
- [ ] Ticket 10 · It survives being switched off

Built by Praveena Rajendran on [LearnTube Guided Projects](https://guidedprojects.learntube.ai).
<!-- learntube:end -->
