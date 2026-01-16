from config.database import CassandraConnection
from loguru import logger

def create_keyspace(session):
    query = """
    CREATE KEYSPACE IF NOT EXISTS library_system
    WITH replication = {
        'class': 'SimpleStrategy',
        'replication_factor': 3
    }
    """
    session.execute(query)
    logger.success("✅ Keyspace library_system créé")

if __name__ == "__main__":
    db = CassandraConnection(keyspace="system")
    session = db.connect()

    create_keyspace(session)

    db.close()
