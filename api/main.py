from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID

from config.database import CassandraConnection
from models.book import BookRepository
from models.user import UserRepository
from models.borrow import BorrowRepository
from models.reservation import ReservationRepository
from models.statistics import StatisticsRepository


app = FastAPI(title="Library API")

# -------------------- CORS --------------------
# Autorise ton front (127.0.0.1:5500) à appeler l'API (127.0.0.1:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Cassandra / Repos (init) --------------------
db = CassandraConnection(keyspace="library_system")
session = None

book_repo = None
user_repo = None
borrow_repo = None
reservation_repo = None
stats_repo = None


@app.on_event("startup")
def on_startup():
    global session, book_repo, user_repo, borrow_repo, reservation_repo, stats_repo
    session = db.connect()

    book_repo = BookRepository(session)
    user_repo = UserRepository(session)
    borrow_repo = BorrowRepository(session)
    reservation_repo = ReservationRepository(session)
    stats_repo = StatisticsRepository(session)


@app.on_event("shutdown")
def on_shutdown():
    global session
    # Si ta classe CassandraConnection gère un close propre, adapte ici.
    # Sinon, au minimum on ferme la session si possible.
    try:
        if session:
            session.shutdown()
    except Exception:
        pass


# -------------------- Helpers --------------------
def parse_uuid(value: str, field_name: str = "user_id") -> UUID:
    try:
        return UUID(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name} invalide (UUID attendu)")


# -------------------- HEALTH --------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------- USERS --------------------
@app.post("/users")
def register_user(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(""),
    address: str = Form(""),
):
    user_id = user_repo.create_user(email, first_name, last_name, phone, address)
    return {"user_id": str(user_id)}


# -------------------- BOOKS --------------------
@app.get("/books/{isbn}")
def get_book(isbn: str):
    book = book_repo.get_book_by_isbn(isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    # Si book est un objet (dataclass ou model), __dict__ marche
    # Si c'est déjà un dict, ça marche aussi (via return book)
    return book.__dict__ if hasattr(book, "__dict__") else book


@app.get("/books")
def list_by_category(category: str):
    return book_repo.get_books_by_category(category)


@app.get("/authors/{author}/books")
def list_by_author(author: str):
    return book_repo.get_books_by_author(author)


# -------------------- BORROWS --------------------
@app.post("/borrows")
def borrow_book(
    user_id: str = Form(...),
    isbn: str = Form(...),
):
    user_uuid = parse_uuid(user_id, "user_id")

    # Vérifier utilisateur
    user = user_repo.get_user(user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Vérifier livre
    book = book_repo.get_book_by_isbn(isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    user_name = f"{user.first_name} {user.last_name}"

    ok = borrow_repo.borrow_book(user.user_id, isbn, book.title, user_name)
    if not ok:
        raise HTTPException(status_code=400, detail="Emprunt impossible")

    return {"success": True}


@app.get("/users/{user_id}/borrows")
def user_borrows(user_id: str):
    user_uuid = parse_uuid(user_id, "user_id")
    return borrow_repo.get_user_borrows(user_uuid)


@app.get("/books/{isbn}/borrows")
def borrows_by_book(isbn: str):
    return borrow_repo.get_borrows_by_book(isbn)


# -------------------- RETURN BOOK --------------------
@app.post("/borrows/return")
def return_book(
    user_id: str = Form(...),
    isbn: str = Form(...),
):
    user_uuid = parse_uuid(user_id, "user_id")

    ok = borrow_repo.return_book(user_uuid, isbn)
    if not ok:
        raise HTTPException(status_code=400, detail="Retour impossible")

    return {"success": True}


# -------------------- RESERVATIONS --------------------
@app.post("/reservations")
def reserve_book(
    user_id: str = Form(...),
    isbn: str = Form(...),
):
    user_uuid = parse_uuid(user_id, "user_id")

    # Vérifier utilisateur
    user = user_repo.get_user(user_uuid)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Vérifier livre
    book = book_repo.get_book_by_isbn(isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Livre introuvable")

    user_name = f"{user.first_name} {user.last_name}"

    ok = reservation_repo.reserve_book(user.user_id, isbn, book.title, user_name)
    if not ok:
        raise HTTPException(status_code=400, detail="Réservation impossible")

    return {"success": True}


@app.get("/reservations/{isbn}")
def list_reservations(isbn: str):
    return reservation_repo.list_reservations_by_isbn(isbn)


# -------------------- STATS --------------------
@app.get("/stats")
def stats(top: int = 5):
    total = stats_repo.get_total_borrows()
    popular = stats_repo.get_top_books(top=top)
    return {"total_borrows": total, "top_books": popular}
