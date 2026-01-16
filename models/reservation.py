from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from cassandra.query import PreparedStatement
from loguru import logger


@dataclass
class Reservation:
    isbn: str
    reservation_date: datetime
    user_id: UUID
    user_name: str
    status: str = "PENDING"


class ReservationRepository:
    def __init__(self, session):
        self.session = session

        # Insert reservation (queue by ISBN)
        self.ps_insert_reservation: PreparedStatement = session.prepare("""
            INSERT INTO reservations_by_book
            (isbn, reservation_date, user_id, user_name, status)
            VALUES (?, ?, ?, ?, ?)
        """)

        # List reservations for a book (FIFO thanks to clustering order)
        self.ps_list_reservations: PreparedStatement = session.prepare("""
            SELECT reservation_date, user_id, user_name, status
            FROM reservations_by_book
            WHERE isbn = ?
        """)

    def add_reservation(self, isbn: str, user_id: UUID, user_name: str) -> bool:
        try:
            now = datetime.now(timezone.utc)
            self.session.execute(self.ps_insert_reservation, (isbn, now, user_id, user_name, "PENDING"))
            logger.success(f"✅ Réservation ajoutée: {isbn} pour {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ add_reservation error: {e}")
            return False

    def list_reservations(self, isbn: str):
        try:
            rows = self.session.execute(self.ps_list_reservations, (isbn,))
            return [
                {
                    "reservation_date": r.reservation_date,
                    "user_id": r.user_id,
                    "user_name": r.user_name,
                    "status": r.status
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"❌ list_reservations error: {e}")
            return []
