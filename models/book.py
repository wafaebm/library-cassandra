from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from cassandra.query import PreparedStatement
from loguru import logger


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    category: str
    publisher: str
    publication_year: int
    total_copies: int
    available_copies: int
    description: str = ""


class BookRepository:
    def __init__(self, session):
        self.session = session

        # ========= INSERTS =========

        # Table lookup par ISBN
        self.ps_insert_isbn: PreparedStatement = session.prepare("""
            INSERT INTO books_by_isbn
            (isbn, title, author, category, publisher, publication_year,
             total_copies, available_copies, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        # Table liste par catégorie
        self.ps_insert_category: PreparedStatement = session.prepare("""
            INSERT INTO books_by_category
            (category, title, isbn, author, publisher, publication_year,
             available_copies, total_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """)

        # ✅ NOUVEAU : Table liste par auteur
        self.ps_insert_author: PreparedStatement = session.prepare("""
            INSERT INTO books_by_author
            (author, title, isbn, category, publisher, publication_year,
             available_copies, total_copies, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """)

        # ========= SELECTS =========

        self.ps_get_by_isbn: PreparedStatement = session.prepare("""
            SELECT * FROM books_by_isbn
            WHERE isbn = ?
        """)

        self.ps_list_by_category: PreparedStatement = session.prepare("""
            SELECT isbn, title, author, available_copies, total_copies
            FROM books_by_category
            WHERE category = ?
        """)

        # ✅ NOUVEAU : liste des livres d’un auteur
        self.ps_list_by_author: PreparedStatement = session.prepare("""
            SELECT isbn, title, category, available_copies, total_copies
            FROM books_by_author
            WHERE author = ?
        """)

    def add_book(self, book: Book) -> bool:
        """Ajoute un livre dans 3 tables (dénormalisation Cassandra)."""
        try:
            # 1) table lookup par ISBN
            self.session.execute(self.ps_insert_isbn, (
                book.isbn, book.title, book.author, book.category,
                book.publisher, book.publication_year,
                book.total_copies, book.available_copies, book.description
            ))

            # 2) table liste par catégorie
            self.session.execute(self.ps_insert_category, (
                book.category, book.title, book.isbn, book.author,
                book.publisher, book.publication_year,
                book.available_copies, book.total_copies
            ))

            # 3) ✅ table liste par auteur
            self.session.execute(self.ps_insert_author, (
                book.author, book.title, book.isbn, book.category,
                book.publisher, book.publication_year,
                book.available_copies, book.total_copies, book.description
            ))

            logger.success(f"✅ Livre ajouté: {book.isbn} - {book.title}")
            return True

        except Exception as e:
            logger.error(f"❌ add_book error: {e}")
            return False

    def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        try:
            row = self.session.execute(self.ps_get_by_isbn, (isbn,)).one()
            if not row:
                return None

            return Book(
                isbn=row.isbn,
                title=row.title,
                author=row.author,
                category=row.category,
                publisher=row.publisher,
                publication_year=row.publication_year,
                total_copies=row.total_copies,
                available_copies=row.available_copies,
                description=row.description or ""
            )
        except Exception as e:
            logger.error(f"❌ get_book_by_isbn error: {e}")
            return None

    def get_books_by_category(self, category: str) -> List[Dict[str, Any]]:
        try:
            rows = self.session.execute(self.ps_list_by_category, (category,))
            return [
                {
                    "isbn": r.isbn,
                    "title": r.title,
                    "author": r.author,
                    "available_copies": r.available_copies,
                    "total_copies": r.total_copies
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"❌ get_books_by_category error: {e}")
            return []

    # ✅ NOUVEAU
    def get_books_by_author(self, author: str) -> List[Dict[str, Any]]:
        try:
            rows = self.session.execute(self.ps_list_by_author, (author,))
            return [
                {
                    "isbn": r.isbn,
                    "title": r.title,
                    "category": r.category,
                    "available_copies": r.available_copies,
                    "total_copies": r.total_copies
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"❌ get_books_by_author error: {e}")
            return []
