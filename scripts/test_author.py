from config.database import CassandraConnection
from models.book import BookRepository, Book

db = CassandraConnection(keyspace="library_system")
session = db.connect()

repo = BookRepository(session)

b = Book(
    isbn="978-9-999999-99-9",
    title="Test Auteur",
    author="Auteur Démo",
    category="Science Fiction",
    publisher="TestPub",
    publication_year=2024,
    total_copies=2,
    available_copies=2,
    description="Livre test auteur"
)

repo.add_book(b)
print(repo.get_books_by_author("Auteur Démo"))

db.close()
