from faker import Faker
from uuid import uuid4
from random import randint, choice
from loguru import logger

from config.database import CassandraConnection
from models.book import BookRepository, Book
from models.user import UserRepository

fake = Faker("fr_FR")

def generate_books(book_repo: BookRepository, count=100):
    categories = ["Science Fiction", "Fantasy", "Thriller", "Romance",
                  "Histoire", "Science", "Biographie", "Philosophie"]
    publishers = ["Gallimard", "Flammarion", "Hachette", "Albin Michel", "Seuil"]

    logger.info(f"📚 Génération de {count} livres...")

    for i in range(count):
        isbn = f"978-{randint(0,9)}-{randint(100000,999999)}-{randint(10,99)}-{randint(0,9)}"

        total = randint(1, 10)
        available = randint(0, total)

        book = Book(
            isbn=isbn,
            title=fake.sentence(nb_words=4)[:-1],
            author=fake.name(),
            category=choice(categories),
            publisher=choice(publishers),
            publication_year=randint(1950, 2024),
            total_copies=total,
            available_copies=available,
            description=fake.text(max_nb_chars=200)
        )

        book_repo.add_book(book)

        if (i + 1) % 10 == 0:
            logger.info(f"  ✅ {i+1}/{count} livres créés")

    logger.success(f"✅ {count} livres générés")

def generate_users(user_repo: UserRepository, count=50):
    logger.info(f"👥 Génération de {count} utilisateurs...")

    ids = []
    for i in range(count):
        user_id = user_repo.create_user(
            email=fake.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone=fake.phone_number(),
            address=fake.address().replace("\n", ", "),
        )
        ids.append(user_id)

        if (i + 1) % 10 == 0:
            logger.info(f"  ✅ {i+1}/{count} utilisateurs créés")

    logger.success(f"✅ {count} utilisateurs générés")
    return ids

if __name__ == "__main__":
    db = CassandraConnection(keyspace="library_system")
    session = db.connect()

    book_repo = BookRepository(session)
    user_repo = UserRepository(session)

    generate_books(book_repo, count=100)
    generate_users(user_repo, count=50)

    logger.success("🎉 Base de données peuplée !")
    db.close()
