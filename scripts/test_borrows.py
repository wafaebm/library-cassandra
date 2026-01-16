from uuid import UUID
from config.database import CassandraConnection
from models.book import BookRepository, Book
from models.user import UserRepository
from models.borrow import BorrowRepository

if __name__ == "__main__":
    db = CassandraConnection(keyspace="library_system")
    session = db.connect()

    book_repo = BookRepository(session)
    user_repo = UserRepository(session)
    borrow_repo = BorrowRepository(session)

    # 1) Crée (ou réutilise) un livre
    book = Book(
        isbn="978-0-111111-11-1",
        title="Le Test",
        author="Moi",
        category="Science Fiction",
        publisher="TestPub",
        publication_year=2020,
        total_copies=2,
        available_copies=2,
        description="Livre pour test emprunt."
    )
    book_repo.add_book(book)

    # 2) Crée un user
    user_id = user_repo.create_user("borrow@test.com", "Bob", "Durand")
    user = user_repo.get_user(user_id)
    user_name = f"{user.first_name} {user.last_name}"

    # 3) Emprunter
    ok = borrow_repo.borrow_book(user_id, book.isbn, book.title, user_name)
    print("BORROW:", ok)

    # 4) Historique
    hist = borrow_repo.get_user_borrows(user_id)
    print("HISTORY:", hist)

    # 5) Retourner
    ok2 = borrow_repo.return_book(user_id, book.isbn)
    print("RETURN:", ok2)

    # 6) Historique après retour
    hist2 = borrow_repo.get_user_borrows(user_id)
    print("HISTORY2:", hist2)

    db.close()
