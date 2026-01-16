# QUERIES - Query patterns & tables Cassandra

## 1) Trouver un livre par ISBN
- **Query**: `SELECT * FROM books_by_isbn WHERE isbn=?`
- **Table**: `books_by_isbn`
- **Partition key**: `isbn`
- **Pourquoi**: lookup direct, O(1), pas de scan.

## 2) Lister les livres d'une catégorie
- **Query**: `SELECT ... FROM books_by_category WHERE category=?`
- **Table**: `books_by_category`
- **Partition key**: `category`
- **Clustering**: `title, isbn` (ordre + unicité)
- **Pourquoi**: navigation rapide par catégorie.

## 3) Trouver tous les livres d'un auteur
- **Query**: `SELECT ... FROM books_by_author WHERE author=?`
- **Table**: `books_by_author`
- **Partition key**: `author`
- **Clustering**: `title, isbn`
- **Pourquoi**: recherche par auteur sans index secondaire.

## 4) Voir le profil d'un utilisateur
- **Query**: `SELECT * FROM users_by_id WHERE user_id=?`
- **Table**: `users_by_id`
- **Partition key**: `user_id`
- **Pourquoi**: accès direct au profil + compteurs.

## 5) Historique des emprunts d'un utilisateur
- **Query**: `SELECT ... FROM borrows_by_user WHERE user_id=?`
- **Table**: `borrows_by_user`
- **Partition key**: `user_id`
- **Clustering**: `borrow_date DESC`
- **Pourquoi**: historique trié (dernier emprunt en premier).

## 6) Qui a emprunté un livre spécifique ?
- **Query**: `SELECT ... FROM borrows_by_book WHERE isbn=?`
- **Table**: `borrows_by_book`
- **Partition key**: `isbn`
- **Clustering**: `borrow_date DESC`
- **Pourquoi**: historique par livre (audit / suivi).

## 7) Livres actuellement empruntés (non retournés)
- **Query**: `SELECT ... FROM active_borrow_by_user_book WHERE user_id=? AND isbn=?`
- **Table**: `active_borrow_by_user_book`
- **Partition key**: `user_id`
- **Clustering**: `isbn`
- **Pourquoi**: savoir si un user a un emprunt actif sur un livre (éviter doublons).

## 8) Réservations en attente pour un livre
- **Query**: `SELECT ... FROM reservations_by_book WHERE isbn=?`
- **Table**: `reservations_by_book`
- **Partition key**: `isbn`
- **Clustering**: `reservation_date`
- **Pourquoi**: file d'attente par livre, triée par date.

## 9) Statistiques globales / livres populaires
- **Queries**:
  - `SELECT total_borrows FROM global_stats WHERE stat_name='GLOBAL'`
  - `SELECT isbn, borrow_count FROM book_popularity`
- **Tables**: `global_stats`, `book_popularity`
- **Pourquoi**: compteurs en temps réel (tables counter).
