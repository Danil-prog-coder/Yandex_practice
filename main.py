import argparse
import os
from datetime import datetime, timezone

import psycopg2
import uvicorn
from fastapi import FastAPI, Query, Response

app = FastAPI()

_conn = None


def db():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            dbname=os.getenv("DB_NAME", "contest"),
        )
        _conn.autocommit = True
    return _conn


def parse_ts(value):
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def fmt_ts(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/book")
def book(
    place_id: int,
    user_id: int,
    time_from: str = Query(alias="from"),
    time_to: str = Query(alias="to"),
):
    try:
        start = parse_ts(time_from)
        end = parse_ts(time_to)
    except ValueError:
        return Response(status_code=400)

    conn = db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM bookings "
            "WHERE place_id = %s AND time_from < %s AND %s < time_to "
            "LIMIT 1",
            (place_id, end, start),
        )
        if cur.fetchone():
            return Response(status_code=409)

        cur.execute(
            "INSERT INTO bookings (user_id, place_id, time_from, time_to) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, place_id, start, end),
        )
    return Response(status_code=200)


@app.get("/booklist")
def booklist(user_id: int | None = None, place_id: int | None = None):
    if user_id is not None:
        column, value = "user_id", user_id
    elif place_id is not None:
        column, value = "place_id", place_id
    else:
        return Response(status_code=400)

    conn = db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, user_id, place_id, time_from, time_to FROM bookings "
            f"WHERE {column} = %s ORDER BY time_from ASC, id ASC",
            (value,),
        )
        rows = cur.fetchall()

    bookings = [
        {
            "id": r[0],
            "user_id": r[1],
            "place_id": r[2],
            "from": fmt_ts(r[3]),
            "to": fmt_ts(r[4]),
        }
        for r in rows
    ]
    return {"bookings": bookings}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    args = p.parse_args()
    uvicorn.run(app, host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
