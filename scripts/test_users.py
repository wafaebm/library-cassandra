from config.database import CassandraConnection
from models.user import UserRepository

if __name__ == "__main__":
    db = CassandraConnection(keyspace="library_system")
    session = db.connect()

    repo = UserRepository(session)

    user_id = repo.create_user(
        email="test@example.com",
        first_name="Alice",
        last_name="Martin",
        phone="0600000000",
        address="Paris"
    )

    user = repo.get_user(user_id)
    print("USER:", user)

    db.close()
