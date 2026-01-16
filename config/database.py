from cassandra.cluster import Cluster
from loguru import logger

class CassandraConnection:
    def __init__(self, hosts=None, port=9042, keyspace="system"):
        self.hosts = hosts or ["127.0.0.1"]
        self.port = port
        self.keyspace = keyspace
        self.cluster = None
        self.session = None

    def connect(self):
        try:
            self.cluster = Cluster(contact_points=self.hosts, port=self.port)
            self.session = self.cluster.connect()
            logger.success(f" Connecté à Cassandra: {self.hosts}:{self.port}")

            # keyspace system existe toujours -> parfait pour un test
            self.session.set_keyspace(self.keyspace)
            logger.success(f"Keyspace actif: {self.keyspace}")
            return self.session

        except Exception as e:
            logger.error(f" Erreur connexion: {e}")
            raise

    def close(self):
        if self.cluster:
            self.cluster.shutdown()
            logger.info(" Connexion fermée")

if __name__ == "__main__":
    db = CassandraConnection()
    session = db.connect()

    rows = session.execute("SELECT release_version FROM system.local")
    for row in rows:
        logger.info(f"Version Cassandra: {row.release_version}")

    db.close()
