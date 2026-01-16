from datetime import datetime, timezone
from uuid import UUID
from cassandra.query import PreparedStatement
from loguru import logger


class BorrowRepository:
    def __init__(self, session):
        self.session = session

        # --- Inserts / Deletes borrow tables ---
        self.ps_insert_borrow_history: PreparedStatement = session.prepare("""
            INSERT INTO borrows_by_user
            (user_id, borrow_date, isbn, book_title, user_name, status, return_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)

        self.ps_upsert_active: PreparedStatement = session.prepare("""
            INSERT INTO active_borrow_by_user_book
            (user_id, isbn, borrow_date, book_title, user_name)
            VALUES (?, ?, ?, ?, ?)
        """)

        self.ps_delete_active: PreparedStatement = session.prepare("""
            DELETE FROM active_borrow_by_user_book
            WHERE user_id = ? AND isbn = ?
        """)

        self.ps_get_active: PreparedStatement = session.prepare("""
            SELECT borrow_date, book_title, user_name
            FROM active_borrow_by_user_book
            WHERE user_id = ? AND isbn = ?
        """)

        self.ps_list_borrows_by_user: PreparedStatement = session.prepare("""
            SELECT isbn, book_title, borrow_date, status, return_date
            FROM borrows_by_user
            WHERE user_id = ?
        """)

        # --- Book reads / updates ---
        self.ps_get_book_isbn: PreparedStatement = session.prepare("""
            SELECT isbn, title, author, category, available_copies, total_copies
            FROM books_by_isbn
            WHERE isbn = ?
        """)

        self.ps_update_book_isbn: PreparedStatement = session.prepare("""
            UPDATE books_by_isbn
            SET available_copies = ?
            WHERE isbn = ?
        """)

        self.ps_update_book_category: PreparedStatement = session.prepare("""
            UPDATE books_by_category
            SET available_copies = ?
            WHERE category = ? AND title = ? AND isbn = ?
        """)

        # ✅ (recommandé) garder cohérent aussi books_by_author
        self.ps_update_book_author: PreparedStatement = session.prepare("""
            UPDATE books_by_author
            SET available_copies = ?
            WHERE author = ? AND title = ? AND isbn = ?
        """)

        # --- User counters ---
        self.ps_get_user_counters: PreparedStatement = session.prepare("""
            SELECT total_borrows, active_borrows
            FROM users_by_id
            WHERE user_id = ?
        """)

        self.ps_update_user_counters: PreparedStatement = session.prepare("""
            UPDATE users_by_id
            SET total_borrows = ?, active_borrows = ?
            WHERE user_id = ?
        """)

        # ✅ NOUVEAU : historique par livre (ISBN)
        self.ps_insert_borrow_by_book: PreparedStatement = session.prepare("""
            INSERT INTO borrows_by_book
            (isbn, borrow_date, user_id, user_name, book_title, status, return_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        
        # --- Stats counters ---
        self.ps_inc_total_borrows: PreparedStatement = session.prepare("""
            UPDATE global_stats
            SET total_borrows = total_borrows + 1
            WHERE stat_name = 'GLOBAL'
        """)

        self.ps_inc_book_popularity: PreparedStatement = session.prepare("""
            UPDATE book_popularity
            SET borrow_count = borrow_count + 1
            WHERE isbn = ?
        """)


        self.ps_list_borrows_by_book: PreparedStatement = session.prepare("""
            SELECT borrow_date, user_id, user_name, status, return_date, book_title
            FROM borrows_by_book
            WHERE isbn = ?
        """)

    def borrow_book(self, user_id: UUID, isbn: str, book_title: str, user_name: str) -> bool:
        """Emprunter un livre (logique simple, sans transaction ACID)."""
        try:
            # 1) Vérifier livre + stock
            book = self.session.execute(self.ps_get_book_isbn, (isbn,)).one()
            if not book:
                logger.warning("Livre introuvable")
                return False

            if book.available_copies is None or book.available_copies <= 0:
                logger.warning("Plus de copies disponibles")
                return False

            # 2) Vérifier si déjà emprunté par cet user (table active)
            active = self.session.execute(self.ps_get_active, (user_id, isbn)).one()
            if active:
                logger.warning("Déjà emprunté par cet utilisateur")
                return False

            borrow_date = datetime.now(timezone.utc)
            new_available = book.available_copies - 1

            # 3) Mettre à jour stock (3 tables)
            self.session.execute(self.ps_update_book_isbn, (new_available, isbn))
            self.session.execute(self.ps_update_book_category, (new_available, book.category, book.title, isbn))
            self.session.execute(self.ps_update_book_author, (new_available, book.author, book.title, isbn))

            # 4) Écrire emprunt (historique + actif)
            self.session.execute(self.ps_insert_borrow_history, (
                user_id, borrow_date, isbn, book_title, user_name, "BORROWED", None
            ))
            self.session.execute(self.ps_upsert_active, (user_id, isbn, borrow_date, book_title, user_name))

            # ✅ 4bis) Écrire aussi dans l’historique par livre
            self.session.execute(self.ps_insert_borrow_by_book, (
                isbn, borrow_date, user_id, user_name, book_title, "BORROWED", None
            ))

            # 5) Mettre à jour compteurs user
            counters = self.session.execute(self.ps_get_user_counters, (user_id,)).one()
            total = (counters.total_borrows or 0) + 1 if counters else 1
            active_count = (counters.active_borrows or 0) + 1 if counters else 1
            self.session.execute(self.ps_update_user_counters, (total, active_count, user_id))

            logger.success(f"✅ Emprunt OK: {isbn} par {user_id}")
            return True

            # 6) Stats (counters)
            self.session.execute(self.ps_inc_total_borrows)
            self.session.execute(self.ps_inc_book_popularity, (isbn,))


        except Exception as e:
            logger.error(f"❌ borrow_book error: {e}")
            return False

    def return_book(self, user_id: UUID, isbn: str) -> bool:
        """Retourner un livre."""
        try:
            # 1) Vérifier emprunt actif
            active = self.session.execute(self.ps_get_active, (user_id, isbn)).one()
            if not active:
                logger.warning("Aucun emprunt actif pour ce user/livre")
                return False

            borrow_date = active.borrow_date  # ✅ super important (clé primaire de l’event)
            return_date = datetime.now(timezone.utc)

            # 2) Lire livre pour category/title/author + stock
            book = self.session.execute(self.ps_get_book_isbn, (isbn,)).one()
            if not book:
                logger.warning("Livre introuvable")
                return False

            new_available = (book.available_copies or 0) + 1
            if book.total_copies is not None:
                new_available = min(new_available, book.total_copies)

            # 3) Mettre à jour stock (3 tables)
            self.session.execute(self.ps_update_book_isbn, (new_available, isbn))
            self.session.execute(self.ps_update_book_category, (new_available, book.category, book.title, isbn))
            self.session.execute(self.ps_update_book_author, (new_available, book.author, book.title, isbn))

            # 4) Supprimer de la table active
            self.session.execute(self.ps_delete_active, (user_id, isbn))

            # 5) Ajouter une ligne RETURNED dans l'historique user (nouvel event)
            self.session.execute(self.ps_insert_borrow_history, (
                user_id, return_date, isbn, active.book_title, active.user_name, "RETURNED", return_date
            ))

            # ✅ 5bis) Mettre à jour l’event borrows_by_book (même PK : isbn + borrow_date + user_id)
            # Upsert Cassandra : on ré-écrit la même ligne avec status RETURNED + return_date
            self.session.execute(self.ps_insert_borrow_by_book, (
                isbn, borrow_date, user_id, active.user_name, active.book_title, "RETURNED", return_date
            ))

            # 6) Mettre à jour compteurs user (active_borrows - 1)
            counters = self.session.execute(self.ps_get_user_counters, (user_id,)).one()
            total = (counters.total_borrows or 0) if counters else 0
            active_count = max((counters.active_borrows or 0) - 1, 0) if counters else 0
            self.session.execute(self.ps_update_user_counters, (total, active_count, user_id))

            logger.success(f"✅ Retour OK: {isbn} par {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ return_book error: {e}")
            return False

    def get_user_borrows(self, user_id: UUID):
        rows = self.session.execute(self.ps_list_borrows_by_user, (user_id,))
        return [
            {
                "isbn": r.isbn,
                "book_title": r.book_title,
                "borrow_date": r.borrow_date,
                "status": r.status,
                "return_date": r.return_date
            }
            for r in rows
        ]

    # ✅ NOUVEAU : query pattern “Qui a emprunté un livre spécifique ?”
    def get_borrows_by_book(self, isbn: str):
        rows = self.session.execute(self.ps_list_borrows_by_book, (isbn,))
        return [dict(r._asdict()) for r in rows]
