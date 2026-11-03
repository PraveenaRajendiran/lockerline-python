
# The app as an image. Data on a volume at /data, every other setting from --env-file, logs to stdout.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY lockerline ./lockerline
COPY seed ./seed

ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

VOLUME ["/data"]

EXPOSE 8080

# The command; the shell expands HOST and PORT (the defaults above, or the env-file's values)
CMD ["sh", "-c", "exec uvicorn lockerline.app:app --host \"$HOST\" --port \"$PORT\""]
