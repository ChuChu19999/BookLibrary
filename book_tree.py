"""
Бинарное дерево — это способ хранить книги в памяти компьютера.

Книги раскладываются по номеру УДК: меньший номер — налево, больший — направо.
Так быстрее найти нужную книгу, чем перебирать весь список подряд.
"""

from book import Book


class BookNode:
    """
    Одна «коробочка» в дереве: внутри книга и две «ветки».

    left — книги с номером УДК меньше, чем у этой.
    right — книги с номером УДК больше.
    """

    # Инициализация объекта Книги
    def __init__(self, book: Book) -> None:
        self.book = book
        # Левая ветка — пока пустая
        self.left: BookNode | None = None
        # Правая ветка — пока пустая
        self.right: BookNode | None = None


class BookBinaryTree:
    """
    Всё дерево книг в памяти.

    Сверху — корень (первая книга). От него идут ветки влево и вправо.
    Дерево упорядочено по номеру УДК, а не по году.
    """

    def __init__(self) -> None:
        # Пока в библиотеке нет ни одной книги — корня нет
        self.root: BookNode | None = None

    @staticmethod
    def _normalize_udc(udc: str) -> str:
        """
        Убирает лишние пробелы в номере УДК.

        Чтобы «004.4» и « 004. 4 » считались одним и тем же номером.
        """
        return udc.strip().replace(" ", "")

    def insert(self, book: Book) -> None:
        """
        Кладёт книгу в дерево.

        Идём от корня: если номер меньше — влево, если больше — вправо.
        Если такой номер уже есть — просто обновляем данные книги.
        """
        book.udc = self._normalize_udc(book.udc)
        if self.root is None:
            self.root = BookNode(book)
            return

        current = self.root
        while True:
            if book.udc < current.book.udc:
                if current.left is None:
                    current.left = BookNode(book)
                    return
                current = current.left
            elif book.udc > current.book.udc:
                if current.right is None:
                    current.right = BookNode(book)
                    return
                current = current.right
            else:
                # Такой номер УДК уже был — заменяем старую карточку новой
                current.book = book
                return

    def find(self, udc: str) -> Book | None:
        """
        Ищет книгу по номеру УДК.

        Нашли — возвращаем книгу. Не нашли — возвращаем None (пусто).
        """
        key = self._normalize_udc(udc)
        current = self.root
        while current is not None:
            if key < current.book.udc:
                current = current.left
            elif key > current.book.udc:
                current = current.right
            else:
                return current.book
        return None

    def delete(self, udc: str) -> bool:
        """
        Убирает книгу из дерева по номеру УДК.

        Возвращает True, если книга была и мы её удалили.
        Возвращает False, если такой книги не было.
        """
        key = self._normalize_udc(udc)
        self.root, removed = self._delete_node(self.root, key)
        return removed

    def _delete_node(
        self, node: BookNode | None, key: str
    ) -> tuple[BookNode | None, bool]:
        """
        Внутренняя помощь: вырезает одну «коробочку» из дерева.

        Бывает по-разному:
        — нет детей: просто убираем коробочку;
        — один ребёнок: поднимаем его наверх;
        — два ребёнка: берём соседнюю книгу с самым маленьким номером справа
          и ставим её вместо удаляемой.
        """
        if node is None:
            return None, False

        if key < node.book.udc:
            node.left, removed = self._delete_node(node.left, key)
            return node, removed

        if key > node.book.udc:
            node.right, removed = self._delete_node(node.right, key)
            return node, removed

        # Вот эту книгу и хотели удалить
        if node.left is None:
            return node.right, True

        if node.right is None:
            return node.left, True

        # Два ребёнка: ищем замену в правой ветке (самый левый там)
        successor_parent = node
        successor = node.right
        while successor.left is not None:
            successor_parent = successor
            successor = successor.left

        node.book = successor.book
        if successor_parent is node:
            successor_parent.right = successor.right
        else:
            successor_parent.left = successor.right

        return node, True

    def _collect_books(self, node: BookNode | None, result: list[Book]) -> None:
        """
        Обходит всё дерево и складывает книги в список.

        Сначала левая ветка, потом сама книга, потом правая — так номера УДК
        получаются по порядку от меньшего к большему.
        """
        if node is None:
            return
        self._collect_books(node.left, result)
        result.append(node.book)
        self._collect_books(node.right, result)

    def all_books(self) -> list[Book]:
        """Возвращает все книги из дерева (по порядку номеров УДК)."""
        books: list[Book] = []
        self._collect_books(self.root, books)
        return books

    def books_sorted_by_year(self) -> list[Book]:
        """
        Все книги, отсортированные по году.

        Сначала собираем из дерева, потом сортируем.
        В программе для таблицы на экране чаще берут книги из базы SQLite.
        """
        books = self.all_books()
        books.sort(key=lambda item: (item.year, item.udc))
        return books

    def clear(self) -> None:
        """Делает дерево пустым — как будто книг не было."""
        self.root = None
