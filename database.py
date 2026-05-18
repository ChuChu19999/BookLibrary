"""
Работа с базой данных SQLite — это файл library.db.

Файл базы library.db создаётся в папке проекта при первом запуске.
Все добавления, изменения и удаления книг сохраняются на диск.
"""

import sqlite3
from pathlib import Path
from book import Book

# Демонстрационный набор при первом запуске или сбросе каталога
INITIAL_BOOKS = [
    Book("821-134.1", "Толстой Л.Н.", "Война и мир", 1869, 3),
    Book("821-134.2", "Толстой Л.Н.", "Анна Каренина", 1877, 2),
    Book("821-3.1", "Достоевский Ф.М.", "Преступление и наказание", 1866, 4),
    Book("821-3.2", "Достоевский Ф.М.", "Идиот", 1869, 1),
    Book("821-111", "Пушкин А.С.", "Евгений Онегин", 1833, 5),
    Book("004.4", "Кнут Д. Э.", "Искусство программирования", 1968, 2),
]


class LibraryDatabase:
    """
    Помощник для файла library.db.

    Там одна таблица books — как тетрадь со строками: одна строка = одна книга.
    У каждой книги номер УДК уникальный — двух одинаковых номеров быть не может.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parent / "library.db"
        self.db_path = Path(db_path)

    @staticmethod
    def normalize_udc(udc: str) -> str:
        """Убирает пробелы в номере УДК перед записью в базу."""
        return udc.strip().replace(" ", "")

    def _connect(self) -> sqlite3.Connection:
        # Открываем файл базы, чтобы читать или писать
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """
        Готовит базу к работе.

        Создаёт таблицу, если её ещё нет.
        Если таблица пустая — кладёт туда стартовые книги.
        """
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    udc TEXT PRIMARY KEY,
                    author TEXT NOT NULL,
                    title TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    copies INTEGER NOT NULL
                )
                """)
            connection.commit()

        if self.is_empty():
            self.seed_initial_books()

    def is_empty(self) -> bool:
        """Проверяет: в базе нет ни одной книги?"""
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS cnt FROM books").fetchone()
        return int(row["cnt"]) == 0

    def upsert_book(self, book: Book) -> None:
        """
        Сохраняет книгу в базу.

        Если такой номер УДК уже был — старая запись заменяется новой.
        """
        book.udc = self.normalize_udc(book.udc)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO books (udc, author, title, year, copies)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(udc) DO UPDATE SET
                    author = excluded.author,
                    title = excluded.title,
                    year = excluded.year,
                    copies = excluded.copies
                """,
                (book.udc, book.author, book.title, book.year, book.copies),
            )
            connection.commit()

    def delete_book(self, udc: str) -> bool:
        """
        Удаляет книгу из базы по номеру УДК.

        True — удалили, False — такой книги в базе не было.
        """
        key = self.normalize_udc(udc)
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM books WHERE udc = ?", (key,))
            connection.commit()
        return cursor.rowcount > 0

    def _row_to_book(self, row: sqlite3.Row) -> Book:
        # Превращаем строку из базы обратно в объект Book
        return Book(
            udc=row["udc"],
            author=row["author"],
            title=row["title"],
            year=int(row["year"]),
            copies=int(row["copies"]),
        )

    def get_all_books(self) -> list[Book]:
        """Читает все книги из базы (по порядку номеров УДК)."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT udc, author, title, year, copies FROM books ORDER BY udc"
            ).fetchall()
        return [self._row_to_book(row) for row in rows]

    def get_books_sorted_by_year(self) -> list[Book]:
        """
        Все книги для отчёта: сначала самый старый год, потом новее.

        Если год одинаковый — сортируем ещё и по номеру УДК.
        """
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT udc, author, title, year, copies
                FROM books
                ORDER BY year ASC, udc ASC
                """).fetchall()
        return [self._row_to_book(row) for row in rows]

    def seed_initial_books(self) -> None:
        """Записывает в базу готовый набор книг (Толстой, Пушкин и др.)."""
        with self._connect() as connection:
            for book in INITIAL_BOOKS:
                normalized = Book(
                    udc=self.normalize_udc(book.udc),
                    author=book.author,
                    title=book.title,
                    year=book.year,
                    copies=book.copies,
                )
                connection.execute(
                    """
                    INSERT INTO books (udc, author, title, year, copies)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(udc) DO UPDATE SET
                        author = excluded.author,
                        title = excluded.title,
                        year = excluded.year,
                        copies = excluded.copies
                    """,
                    (
                        normalized.udc,
                        normalized.author,
                        normalized.title,
                        normalized.year,
                        normalized.copies,
                    ),
                )
            connection.commit()

    def reset_to_initial(self) -> None:
        """
        Стирает все книги в базе и снова кладёт стартовый набор.

        Как кнопка «вернуть как было в начале».
        """
        with self._connect() as connection:
            connection.execute("DELETE FROM books")
            connection.commit()
        self.seed_initial_books()
