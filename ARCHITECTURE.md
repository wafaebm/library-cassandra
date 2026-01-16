# ARCHITECTURE - Library Cassandra System

## 1) Vue d’ensemble
Le projet est un système de gestion de bibliothèque numérique conçu pour être **scalable horizontalement** et **hautement disponible**.
On utilise :
- **Apache Cassandra** (cluster distribué) pour stocker livres/utilisateurs/emprunts
- **Python** (cassandra-driver) pour la logique métier
- **CLI Click** pour interagir avec le système (CRUD + emprunts + stats)

## 2) Architecture technique (flux)
1. L’utilisateur lance une commande CLI (`python -m cli.main ...`)
2. Le CLI appelle des repositories Python (BookRepository, UserRepository, BorrowRepository, StatisticsRepository)
3. Les repositories exécutent des **prepared statements** via `cassandra-driver`
4. Cassandra écrit/lit dans des tables **dénormalisées** (une table par requête)

## 3) Cluster Cassandra
- Cluster local Docker : **3 nœuds**
- Keyspace : `library_system`
- Replication factor : `3` (données répliquées sur 3 nœuds)

Objectif : simuler un environnement réel de bibliothèque universitaire (beaucoup d’utilisateurs/livres, charge élevée).

## 4) Modélisation orientée requêtes (principe Cassandra)
Contrairement au SQL, on ne fait pas de JOIN.
On part des besoins (query patterns) et on crée **une table par requête**.

➡️ Conséquence : **dénormalisation** (données dupliquées) est normale.
Exemple : un livre est stocké dans plusieurs tables (`books_by_isbn`, `books_by_category`, `books_by_author`) pour permettre des lectures rapides.

## 5) Tables principales et rôle
### Livres
- `books_by_isbn` : lookup direct par ISBN
- `books_by_category` : liste des livres par catégorie
- `books_by_author` : liste des livres par auteur

### Utilisateurs
- `users_by_id` : profil utilisateur + compteurs (total_borrows, active_borrows)

### Emprunts
- `borrows_by_user` : historique des emprunts d’un utilisateur (trié par date)
- `active_borrow_by_user_book` : emprunt actif pour éviter qu’un user emprunte deux fois le même livre
- `borrows_by_book` : historique par livre (qui a emprunté ce livre ?)

### Réservations
- `reservations_by_book` : file d’attente des réservations pour un ISBN

### Statistiques
- `global_stats` : compteur global (total des emprunts)
- `book_popularity` : compteur par livre (popularité)

## 6) Partition key et clustering key (simple)
- **Partition key** : décide sur quel nœud vivent les données (répartition + perf)
- **Clustering key** : ordre des lignes dans une partition (ex: `borrow_date DESC`)

Exemples :
- `borrows_by_user (user_id, borrow_date DESC)` permet d’avoir l’historique trié.
- `borrows_by_book (isbn, borrow_date DESC)` permet de voir rapidement les derniers emprunts d’un livre.

## 7) Cohérence vs Disponibilité (rappel)
Cassandra favorise la disponibilité.
On accepte une cohérence éventuelle sur certaines écritures (ex: stock dans plusieurs tables).
Le système reste performant et disponible sous charge.

## 8) Limites / améliorations possibles
- Réservations automatiques (quand un livre est rendu → attribuer au prochain)
- Benchmarks lecture/écriture
- Tests unitaires (pytest)
- API REST (FastAPI/Flask) en bonus
