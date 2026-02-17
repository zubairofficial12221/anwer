import os
from datetime import datetime, time

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

from db import get_connection


load_dotenv()

TICKET_PRICE_CENTS = 1500  # $15.00


def create_app() -> Flask:
    app = Flask(__name__)

    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": cors_origins or "*"}})

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    def _db_unavailable(err: Exception):
        return (
            jsonify(
                {
                    "error": "MySQL is not reachable. Start XAMPP MySQL, create/import the schema, then try again.",
                    "details": str(err),
                }
            ),
            503,
        )

    def _normalize_title(title: str) -> str:
        return (title or "").strip()

    def _default_showtime_dt() -> datetime:
        # Today at 19:00 local time (matches schema.sql seed)
        today = datetime.now().date()
        return datetime.combine(today, time(hour=19, minute=0, second=0))

    def _get_or_create_showtime_id(cursor, movie_title: str) -> int:
        title = _normalize_title(movie_title)
        if not title:
            raise ValueError("movie_title is required")

        cursor.execute("SELECT id FROM movies WHERE title = %s", (title,))
        row = cursor.fetchone()
        if row:
            movie_id = int(row[0])
        else:
            cursor.execute("INSERT INTO movies (title) VALUES (%s)", (title,))
            movie_id = int(cursor.lastrowid)

        starts_at = _default_showtime_dt()
        cursor.execute(
            "SELECT id FROM showtimes WHERE movie_id = %s AND starts_at = %s",
            (movie_id, starts_at),
        )
        row = cursor.fetchone()
        if row:
            return int(row[0])

        cursor.execute(
            "INSERT INTO showtimes (movie_id, starts_at) VALUES (%s, %s)",
            (movie_id, starts_at),
        )
        return int(cursor.lastrowid)

    @app.get("/api/seats")
    def get_seats():
        movie_title = request.args.get("movie_title", "")
        title = _normalize_title(movie_title)
        if not title:
            return jsonify({"error": "movie_title is required"}), 400

        try:
            conn = get_connection()
        except mysql.connector.Error as e:
            return _db_unavailable(e)
        try:
            cur = conn.cursor()
            showtime_id = _get_or_create_showtime_id(cur, title)

            cur.execute(
                "SELECT seat_code FROM booking_seats WHERE showtime_id = %s",
                (showtime_id,),
            )
            occupied = sorted([r[0] for r in cur.fetchall()])
            conn.commit()
            return jsonify({"movie_title": title, "showtime_id": showtime_id, "occupied": occupied})
        finally:
            conn.close()

    @app.post("/api/bookings")
    def create_booking():
        payload = request.get_json(silent=True) or {}
        title = _normalize_title(payload.get("movie_title", ""))
        seats = payload.get("seats", [])
        customer_email = (payload.get("customer_email") or "").strip() or None

        if not title:
            return jsonify({"error": "movie_title is required"}), 400
        if not isinstance(seats, list) or not seats:
            return jsonify({"error": "seats must be a non-empty array"}), 400

        # Normalize and dedupe seats
        normalized_seats = []
        seen = set()
        for s in seats:
            if not isinstance(s, str):
                continue
            code = s.strip().upper()
            if not code or code in seen:
                continue
            seen.add(code)
            normalized_seats.append(code)

        if not normalized_seats:
            return jsonify({"error": "no valid seat codes provided"}), 400

        try:
            conn = get_connection()
        except mysql.connector.Error as e:
            return _db_unavailable(e)
        try:
            cur = conn.cursor()
            showtime_id = _get_or_create_showtime_id(cur, title)

            total_price_cents = len(normalized_seats) * TICKET_PRICE_CENTS

            # Create booking header
            cur.execute(
                "INSERT INTO bookings (showtime_id, customer_email, total_price_cents) VALUES (%s, %s, %s)",
                (showtime_id, customer_email, total_price_cents),
            )
            booking_id = int(cur.lastrowid)

            # Insert seats (will fail if seat already booked due to unique constraint)
            try:
                cur.executemany(
                    "INSERT INTO booking_seats (booking_id, showtime_id, seat_code) VALUES (%s, %s, %s)",
                    [(booking_id, showtime_id, code) for code in normalized_seats],
                )
            except Exception as e:
                conn.rollback()
                return jsonify({"error": "One or more seats are already booked.", "details": str(e)}), 409

            conn.commit()
            return (
                jsonify(
                    {
                        "booking_id": booking_id,
                        "movie_title": title,
                        "showtime_id": showtime_id,
                        "seats": normalized_seats,
                        "total_price_cents": total_price_cents,
                    }
                ),
                201,
            )
        finally:
            conn.close()

    @app.get("/api/bookings/<int:booking_id>")
    def get_booking(booking_id: int):
        try:
            conn = get_connection()
        except mysql.connector.Error as e:
            return _db_unavailable(e)
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT b.id AS booking_id, b.customer_email, b.total_price_cents, b.created_at,
                       s.id AS showtime_id, s.starts_at,
                       m.title AS movie_title
                FROM bookings b
                JOIN showtimes s ON s.id = b.showtime_id
                JOIN movies m ON m.id = s.movie_id
                WHERE b.id = %s
                """,
                (booking_id,),
            )
            booking = cur.fetchone()
            if not booking:
                return jsonify({"error": "Booking not found"}), 404

            cur.execute(
                "SELECT seat_code FROM booking_seats WHERE booking_id = %s ORDER BY seat_code ASC",
                (booking_id,),
            )
            seats = [r["seat_code"] for r in cur.fetchall()]

            return jsonify({**booking, "seats": seats})
        finally:
            conn.close()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

