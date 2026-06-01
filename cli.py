"""
Консольный интерфейс программы «Библиотека книг».

Меню в терминале: добавление, удаление, отчёт, просмотр каталога.
"""

from book import Book
from library import LibraryCatalog, create_catalog

COLUMN_WIDTHS = {
    "udc": 14,
    "author": 22,
    "title": 32,
    "year": 6,
    "copies": 12,
}

COLUMN_HEADERS = {
    "udc": "УДК",
    "author": "Автор",
    "title": "Название",
    "year": "Год",
    "copies": "Экземпляры",
}


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text.ljust(width)
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def print_books_table(books: list[Book]) -> None:
    """Печатает список книг в виде таблицы в терминале."""
    if not books:
        print("\nВ библиотеке пока нет книг.\n")
        return

    header = " | ".join(
        _truncate(COLUMN_HEADERS[key], COLUMN_WIDTHS[key])
        for key in ("udc", "author", "title", "year", "copies")
    )
    separator = "-+-".join("-" * COLUMN_WIDTHS[key] for key in COLUMN_WIDTHS)

    print()
    print(header)
    print(separator)
    for book in books:
        row = book.as_row()
        line = " | ".join(
            _truncate(row[i], COLUMN_WIDTHS[key])
            for i, key in enumerate(("udc", "author", "title", "year", "copies"))
        )
        print(line)
    print(f"\nВсего книг: {len(books)}\n")


def _read_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Поле не может быть пустым. Повторите ввод.")


def _read_int(prompt: str, min_value: int = 0) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            number = int(raw)
        except ValueError:
            print("Введите целое число.")
            continue
        if number < min_value:
            print(f"Число не может быть меньше {min_value}.")
            continue
        return number


def read_book_from_input() -> Book:
    """Запрашивает у пользователя все поля книги."""
    udc = _read_non_empty("Номер УДК: ")
    author = _read_non_empty("Автор (фамилия и инициалы): ")
    title = _read_non_empty("Название: ")
    year = _read_int("Год издания: ", min_value=0)
    copies = _read_int("Количество экземпляров: ", min_value=0)
    return Book(udc=udc, author=author, title=title, year=year, copies=copies)


def _confirm(message: str) -> bool:
    answer = input(f"{message} (д/н): ").strip().lower()
    return answer in ("д", "да", "y", "yes")


class LibraryConsole:
    """Главный цикл консольной программы."""

    def __init__(self, catalog: LibraryCatalog) -> None:
        self.catalog = catalog

    def show_menu(self) -> None:
        print("\n" + "=" * 50)
        print("  Библиотека книг")
        print("=" * 50)
        print("  1. Показать каталог (сортировка по году)")
        print("  2. Добавить книгу")
        print("  3. Удалить книгу")
        print("  4. Отчёт по годам")
        print("  5. Найти книгу по УДК")
        print("  6. Загрузить начальные данные")
        print("  0. Выход")
        print("=" * 50)

    def action_list(self) -> None:
        books = self.catalog.books_sorted_by_year()
        print_books_table(books)

    def action_add(self) -> None:
        print("\n--- Добавление книги ---")
        book = read_book_from_input()
        existed = self.catalog.insert(book)
        if existed:
            print(
                "Книга с таким УДК уже была в каталоге. Запись обновлена в базе и в дереве."
            )
        else:
            print("Книга добавлена в бинарное дерево и сохранена в SQLite.")

    def action_delete(self) -> None:
        print("\n--- Удаление книги ---")
        udc = _read_non_empty("Номер УДК книги для удаления: ")
        if not self.catalog.delete(udc):
            print(f"Книга с УДК «{udc}» не найдена в библиотеке.")
            return
        print("Книга удалена из дерева и из базы SQLite.")

    def action_report(self) -> None:
        print("\n--- Отчёт по годам ---")
        self.catalog.reload_from_database()
        books = self.catalog.books_sorted_by_year()

        if not books:
            print("В библиотеке пока нет ни одной книги.")
            print("Добавьте книгу или выберите пункт «Загрузить начальные данные».")
            return

        years = [book.year for book in books]
        print(f"Всего книг: {len(books)}")
        print(f"Самый ранний год: {min(years)}")
        print(f"Самый поздний год: {max(years)}")
        print("\nСписок по годам (от старого к новому):")
        for book in books:
            print(f"  {book.year} — «{book.title}», {book.author} (УДК {book.udc})")
        print()
        print_books_table(books)

    def action_find(self) -> None:
        print("\n--- Поиск по УДК ---")
        udc = _read_non_empty("Номер УДК: ")
        book = self.catalog.find(udc)
        if book is None:
            print(f"Книга с УДК «{udc}» не найдена.")
            return
        print("\nНайдена книга:")
        print_books_table([book])

    def action_reset(self) -> None:
        print("\n--- Загрузка начальных данных ---")
        if not _confirm(
            "Каталог в базе будет заменён начальным набором книг. Продолжить?"
        ):
            print("Операция отменена.")
            return
        self.catalog.reset_to_initial_data()
        print("Каталог сброшен к начальному набору.")
        self.action_list()

    def run(self) -> None:
        """Запускает программу до выхода пользователя."""
        print("Добро пожаловать в библиотеку книг.")
        print("Данные хранятся в файле library.db в папке проекта.")
        self.action_list()

        actions = {
            "1": self.action_list,
            "2": self.action_add,
            "3": self.action_delete,
            "4": self.action_report,
            "5": self.action_find,
            "6": self.action_reset,
        }

        while True:
            self.show_menu()
            choice = input("Выберите пункт меню: ").strip()

            if choice == "0":
                print("До свидания.")
                break

            action = actions.get(choice)
            if action is None:
                print("Неверный пункт меню. Введите число от 0 до 6.")
                continue

            try:
                action()
            except KeyboardInterrupt:
                print("\nОперация прервана.")
            except EOFError:
                print("\nВвод завершён. Выход из программы.")
                break


def run_app() -> None:
    """Создаёт каталог и запускает консольное меню."""
    catalog = create_catalog()
    LibraryConsole(catalog).run()
