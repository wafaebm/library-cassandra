-- Keyspace
USE library_system;

-- 1) Trouver un livre par ISBN
CREATE TABLE IF NOT EXISTS books_by_isbn (
  isbn text PRIMARY KEY,
  title text,
  author text,
  category text,
  publisher text,
  publication_year int,
  total_copies int,
  available_copies int,
  description text
);

-- 2) Lister les livres d'une catégorie (tri par titre)
CREATE TABLE IF NOT EXISTS books_by_category (
  category text,
  title text,
  isbn text,
  author text,
  publisher text,
  publication_year int,
  available_copies int,
  total_copies int,
  PRIMARY KEY ((category), title, isbn)
);

-- 3) Profil utilisateur
CREATE TABLE IF NOT EXISTS users_by_id (
  user_id uuid PRIMARY KEY,
  email text,
  first_name text,
  last_name text,
  phone text,
  address text,
  registration_date timestamp,
  total_borrows int,
  active_borrows int
);

-- 4) Historique des emprunts d'un utilisateur (tri par date desc)
CREATE TABLE IF NOT EXISTS borrows_by_user (
  user_id uuid,
  borrow_date timestamp,
  isbn text,
  book_title text,
  user_name text,
  status text,          -- 'BORROWED' ou 'RETURNED'
  return_date timestamp,
  PRIMARY KEY ((user_id), borrow_date, isbn)
) WITH CLUSTERING ORDER BY (borrow_date DESC);

-- 5) Emprunt actif (pour retour/check rapide)
CREATE TABLE IF NOT EXISTS active_borrow_by_user_book (
  user_id uuid,
  isbn text,
  borrow_date timestamp,
  book_title text,
  user_name text,
  PRIMARY KEY ((user_id), isbn)
);

CREATE TABLE IF NOT EXISTS books_by_author (
  author text,
  title text,
  isbn text,
  category text,
  publisher text,
  publication_year int,
  available_copies int,
  total_copies int,
  description text,
  PRIMARY KEY ((author), title, isbn)
) WITH CLUSTERING ORDER BY (title ASC);

CREATE TABLE IF NOT EXISTS borrows_by_book (
  isbn text,
  borrow_date timestamp,
  user_id uuid,
  user_name text,
  book_title text,
  status text,
  return_date timestamp,
  PRIMARY KEY ((isbn), borrow_date, user_id)
) WITH CLUSTERING ORDER BY (borrow_date DESC);

CREATE TABLE IF NOT EXISTS reservations_by_book (
  isbn text,
  reservation_date timestamp,
  user_id uuid,
  user_name text,
  status text,
  PRIMARY KEY ((isbn), reservation_date, user_id)
) WITH CLUSTERING ORDER BY (reservation_date ASC);

CREATE TABLE IF NOT EXISTS global_stats (
  stat_name text PRIMARY KEY,
  total_borrows counter
);

CREATE TABLE IF NOT EXISTS book_popularity (
  isbn text PRIMARY KEY,
  borrow_count counter
);
