from cassandra.query import PreparedStatement
from loguru import logger

class StatisticsRepository:
    def __init__(self, session):
        self.session = session

        self.ps_get_total_borrows: PreparedStatement = session.prepare("""
            SELECT total_borrows FROM global_stats WHERE stat_name = 'GLOBAL'
        """)

        # On récupère tout et on triera côté Python (simple pour le projet)
        self.ps_get_all_popularity: PreparedStatement = session.prepare("""
            SELECT isbn, borrow_count FROM book_popularity
        """)

    def get_total_borrows(self) -> int:
        try:
            row = self.session.execute(self.ps_get_total_borrows).one()
            return int(row.total_borrows) if row and row.total_borrows is not None else 0
        except Exception as e:
            logger.error(f"❌ get_total_borrows error: {e}")
            return 0

    def get_top_books(self, limit: int = 10):
        try:
            rows = list(self.session.execute(self.ps_get_all_popularity))
            # borrow_count est un counter → cast en int
            rows_sorted = sorted(rows, key=lambda r: int(r.borrow_count or 0), reverse=True)
            return [
                {"isbn": r.isbn, "borrow_count": int(r.borrow_count or 0)}
                for r in rows_sorted[:limit]
            ]
        except Exception as e:
            logger.error(f"❌ get_top_books error: {e}")
            return []
