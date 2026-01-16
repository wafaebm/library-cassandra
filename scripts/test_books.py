from config.database import CassandraConnection
from models.book import BookRepository, Book

if __name__ == "__main__":
    db = CassandraConnection(keyspace="library_system")
    session = db.connect()

    repo = BookRepository(session)

    book = Book(
        isbn="978-0-123456-78-9",
        title="Dune",
        author="Frank Herbert",
        category="Science Fiction",
        publisher="Ace",
        publication_year=1965,
        total_copies=5,
        available_copies=5,
        description="Classique SF."
    )

    repo.add_book(book)

    found = repo.get_book_by_isbn(book.isbn)
    print("FOUND:", found)

    books = repo.get_books_by_category("Science Fiction")
    print("BY CATEGORY:", books)

    db.close()
