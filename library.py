"""
Связывает базу на диске и дерево в памяти.

Когда ты что-то меняешь в программе — меняется и файл library.db,
и дерево книг в памяти. Так они всегда показывают одно и то же.
"""

from book import Book
from book_tree import BookBinaryTree
from database import LibraryDatabase


class LibraryCatalog:
    """
    Главный «пульт» библиотеки для консольной программы.

    Сюда приходят команды: добавить, удалить, показать список.
    """

    def __init__(self, database: LibraryDatabase) -> None:
        self.database = database
        self.tree = BookBinaryTree()
        # При старте читаем книги из базы и строим из них дерево
        self.reload_from_database()

    def reload_from_database(self) -> None:
        """
        Заново читает все книги из файла library.db и строит дерево.

        Нужно после сброса или когда базу обновили снаружи.
        """
        self.tree.clear()
        for book in self.database.get_all_books():
            self.tree.insert(book)

    def find(self, udc: str) -> Book | None:
        """Ищет книгу по номеру УДК в дереве."""
        return self.tree.find(udc)

    def insert(self, book: Book) -> bool:
        """
        Добавляет книгу.

        Сначала пишем в базу на диске, потом — в дерево в памяти.
        Возвращает True, если книга с таким УДК уже была (мы её обновили).
        """
        existed = self.tree.find(book.udc) is not None
        self.database.upsert_book(book)
        self.tree.insert(book)
        return existed

    def delete(self, udc: str) -> bool:
        """
        Удаляет книгу и из дерева, и из базы.

        False — если такой книги не нашли.
        """
        if not self.tree.delete(udc):
            return False
        self.database.delete_book(udc)
        return True

    def books_sorted_by_year(self) -> list[Book]:
        """Список всех книг для вывода в консоль — от старого года к новому."""
        return self.database.get_books_sorted_by_year()

    def reset_to_initial_data(self) -> None:
        """
        Возвращает библиотеку к начальному набору книг.

        В базе снова будут только те книги, что заданы в программе изначально.
        """
        self.database.reset_to_initial()
        self.reload_from_database()


def create_catalog() -> LibraryCatalog:
    """
    Запускается при старте программы.

    Создаёт файл library.db, если его ещё нет, и готовит каталог.
    """
    database = LibraryDatabase()
    database.initialize()
    return LibraryCatalog(database)
