import click
from uuid import UUID
from tabulate import tabulate

from config.database import CassandraConnection
from models.book import BookRepository, Book
from models.user import UserRepository
from models.borrow import BorrowRepository
from models.reservation import ReservationRepository
from models.statistics import StatisticsRepository


@click.group()
def cli():
    """📚 Système de Gestion de Bibliothèque"""
    pass

# Connexion globale
db = CassandraConnection(keyspace="library_system")
session = db.connect()

book_repo = BookRepository(session)
user_repo = UserRepository(session)
borrow_repo = BorrowRepository(session)
reservation_repo = ReservationRepository(session)
stats_repo = StatisticsRepository(session)


# ========== BOOKS ==========

@cli.group()
def books():
    """Gestion des livres"""
    pass

@books.command()
@click.option('--isbn', prompt='ISBN')
@click.option('--title', prompt='Titre')
@click.option('--author', prompt='Auteur')
@click.option('--category', prompt='Catégorie')
@click.option('--publisher', prompt='Éditeur')
@click.option('--year', prompt='Année', type=int)
@click.option('--copies', prompt='Nombre de copies', type=int, default=1)
@click.option('--description', prompt='Description', default="")
def add(isbn, title, author, category, publisher, year, copies, description):
    book = Book(
        isbn=isbn,
        title=title,
        author=author,
        category=category,
        publisher=publisher,
        publication_year=year,
        total_copies=copies,
        available_copies=copies,
        description=description
    )

    if book_repo.add_book(book):
        click.echo(click.style(f"✅ Livre ajouté: {title}", fg='green'))
    else:
        click.echo(click.style("❌ Erreur ajout livre", fg='red'))

@books.command()
@click.option('--isbn', prompt='ISBN')
def search(isbn):
    book = book_repo.get_book_by_isbn(isbn)
    if book:
        data = [
            ["ISBN", book.isbn],
            ["Titre", book.title],
            ["Auteur", book.author],
            ["Catégorie", book.category],
            ["Éditeur", book.publisher],
            ["Année", book.publication_year],
            ["Copies dispo", f"{book.available_copies}/{book.total_copies}"],
        ]
        click.echo("\n" + tabulate(data, tablefmt="grid"))
    else:
        click.echo(click.style("❌ Livre introuvable", fg='red'))

@books.command(name="list-by-category")
@click.option('--category', prompt='Catégorie')
def list_by_category(category):
    books = book_repo.get_books_by_category(category)
    if books:
        data = [[b["isbn"], b["title"], b["author"], f"{b['available_copies']}/{b['total_copies']}"] for b in books]
        headers = ['ISBN', 'Titre', 'Auteur', 'Dispo']
        click.echo("\n" + tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo(click.style("Aucun livre trouvé", fg='yellow'))

@books.command()
@click.option('--author', prompt='Auteur', help='Nom de l’auteur')
def list_by_author(author):
    """Lister les livres d'un auteur"""
    books = book_repo.get_books_by_author(author)

    if books:
        data = [[b['isbn'], b['title'], b['category'], f"{b['available_copies']}/{b['total_copies']}"]
                for b in books]
        headers = ['ISBN', 'Titre', 'Catégorie', 'Dispo']
        click.echo("\n" + tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo(click.style("Aucun livre trouvé pour cet auteur", fg='yellow'))

# ========== USERS ==========

@cli.group()
def users():
    """Gestion des utilisateurs"""
    pass

@users.command()
@click.option('--email', prompt='Email')
@click.option('--first-name', prompt='Prénom')
@click.option('--last-name', prompt='Nom')
@click.option('--phone', prompt='Téléphone', default="")
@click.option('--address', prompt='Adresse', default="")
def register(email, first_name, last_name, phone, address):
    user_id = user_repo.create_user(email, first_name, last_name, phone=phone, address=address)
    click.echo(click.style(f"✅ Utilisateur créé: {user_id}", fg='green'))

@users.command()
@click.option('--user-id', prompt='User ID')
def profile(user_id):
    user = user_repo.get_user(UUID(user_id))
    if user:
        data = [
            ["ID", user.user_id],
            ["Nom", f"{user.first_name} {user.last_name}"],
            ["Email", user.email],
            ["Inscription", user.registration_date],
            ["Emprunts totaux", user.total_borrows],
            ["Emprunts actifs", user.active_borrows],
        ]
        click.echo("\n" + tabulate(data, tablefmt="grid"))
    else:
        click.echo(click.style("❌ Utilisateur introuvable", fg='red'))

# ========== BORROWS ==========

@cli.group()
def borrows():
    """Gestion des emprunts"""
    pass

@borrows.command()
@click.option('--user-id', prompt='User ID')
@click.option('--isbn', prompt='ISBN')
def borrow(user_id, isbn):
    user = user_repo.get_user(UUID(user_id))
    book = book_repo.get_book_by_isbn(isbn)

    if not user:
        click.echo(click.style("❌ Utilisateur introuvable", fg='red'))
        return
    if not book:
        click.echo(click.style("❌ Livre introuvable", fg='red'))
        return

    user_name = f"{user.first_name} {user.last_name}"
    if borrow_repo.borrow_book(user.user_id, isbn, book.title, user_name):
        click.echo(click.style(f"✅ Emprunt réussi: {book.title}", fg='green'))
    else:
        click.echo(click.style("❌ Emprunt échoué", fg='red'))

@borrows.command(name="return-book")
@click.option('--user-id', prompt='User ID')
@click.option('--isbn', prompt='ISBN')
def return_book(user_id, isbn):
    if borrow_repo.return_book(UUID(user_id), isbn):
        click.echo(click.style("✅ Livre retourné", fg='green'))
    else:
        click.echo(click.style("❌ Retour échoué", fg='red'))

@borrows.command("who-borrowed")
@click.option('--isbn', prompt='ISBN', help='ISBN du livre')
def who_borrowed(isbn):
    """Voir qui a emprunté un livre (historique par ISBN)"""
    borrows = borrow_repo.get_borrows_by_book(isbn)

    if borrows:
        data = [[
            b.get('user_name'),
            str(b.get('user_id')),
            b.get('borrow_date'),
            b.get('status'),
            b.get('return_date')
        ] for b in borrows]

        headers = ['Utilisateur', 'User ID', 'Date emprunt', 'Statut', 'Date retour']
        click.echo("\n" + tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo(click.style("Aucun emprunt trouvé pour cet ISBN", fg='yellow'))

@borrows.command("reserve")
@click.option('--user-id', prompt='User ID', help="UUID de l'utilisateur")
@click.option('--isbn', prompt='ISBN', help='ISBN du livre')
def reserve(user_id, isbn):
    """Réserver un livre (ajoute dans la file d'attente)"""
    user = user_repo.get_user(UUID(user_id))
    book = book_repo.get_book_by_isbn(isbn)

    if not user:
        click.echo(click.style("❌ Utilisateur introuvable", fg='red'))
        return

    if not book:
        click.echo(click.style("❌ Livre introuvable", fg='red'))
        return

    user_name = f"{user.first_name} {user.last_name}"

    if reservation_repo.add_reservation(isbn, user.user_id, user_name):
        click.echo(click.style(f"✅ Réservation ajoutée pour {book.title}", fg='green'))
    else:
        click.echo(click.style("❌ Erreur réservation", fg='red'))


@borrows.command("list-reservations")
@click.option('--isbn', prompt='ISBN', help='ISBN du livre')
def list_reservations(isbn):
    """Lister les réservations d'un livre (FIFO)"""
    reservations = reservation_repo.list_reservations(isbn)

    if reservations:
        data = [[
            r['reservation_date'],
            r['user_name'],
            str(r['user_id']),
            r['status']
        ] for r in reservations]

        headers = ['Date', 'Utilisateur', 'User ID', 'Statut']
        click.echo("\n" + tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo(click.style("Aucune réservation pour cet ISBN", fg='yellow'))

@cli.command("stats")
@click.option("--top", default=10, show_default=True, help="Nombre de livres dans le top")
def stats(top):
    """Afficher les statistiques globales"""
    total = stats_repo.get_total_borrows()
    top_books = stats_repo.get_top_books(limit=top)

    click.echo(f"\n📊 Total emprunts: {total}\n")

    if top_books:
        data = [[b["isbn"], b["borrow_count"]] for b in top_books]
        headers = ["ISBN", "Nb emprunts"]
        click.echo(tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo("Aucun livre dans les stats.")


@borrows.command()
@click.option('--user-id', prompt='User ID')
def history(user_id):
    borrows = borrow_repo.get_user_borrows(UUID(user_id))
    if borrows:
        data = [[b["isbn"], b["book_title"], b["borrow_date"], b["status"]] for b in borrows]
        headers = ['ISBN', 'Titre', 'Date', 'Statut']
        click.echo("\n" + tabulate(data, headers=headers, tablefmt="grid"))
    else:
        click.echo(click.style("Aucun emprunt", fg='yellow'))

if __name__ == '__main__':
    try:
        cli()
    finally:
        db.close()


