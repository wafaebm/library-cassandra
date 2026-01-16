from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4
from cassandra.query import PreparedStatement
from loguru import logger
from datetime import datetime, timezone

@dataclass
class User:
    user_id: UUID
    email: str
    first_name: str
    last_name: str
    phone: str = ""
    address: str = ""
    registration_date: datetime = None
    total_borrows: int = 0
    active_borrows: int = 0

class UserRepository:
    def __init__(self, session):
        self.session = session

        self.ps_insert: PreparedStatement = session.prepare("""
            INSERT INTO users_by_id
            (user_id, email, first_name, last_name, phone, address,
             registration_date, total_borrows, active_borrows)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        self.ps_get: PreparedStatement = session.prepare("""
            SELECT * FROM users_by_id WHERE user_id = ?
        """)

    def create_user(self, email: str, first_name: str, last_name: str,
                    phone: str = "", address: str = "") -> UUID:
        user_id = uuid4()
        reg_date = datetime.now(timezone.utc)

        try:
            self.session.execute(self.ps_insert, (
                user_id, email, first_name, last_name, phone, address,
                reg_date, 0, 0
            ))
            logger.success(f"✅ Utilisateur créé: {user_id}")
            return user_id
        except Exception as e:
            logger.error(f"❌ create_user error: {e}")
            raise

    def get_user(self, user_id: UUID) -> Optional[User]:
        try:
            row = self.session.execute(self.ps_get, (user_id,)).one()
            if not row:
                return None

            return User(
                user_id=row.user_id,
                email=row.email,
                first_name=row.first_name,
                last_name=row.last_name,
                phone=row.phone or "",
                address=row.address or "",
                registration_date=row.registration_date,
                total_borrows=row.total_borrows or 0,
                active_borrows=row.active_borrows or 0
            )
        except Exception as e:
            logger.error(f"❌ get_user error: {e}")
            return None
