"""
Окно программы на tkinter — то, что видит пользователь.

Кнопки, поля для ввода и таблица со списком книг.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from book import Book
from library import LibraryCatalog, create_catalog


class LibraryApp:
    """
    Всё главное окно «Библиотека книг».

    Сверху — поля, куда вводишь данные о книге.
    Посередине — таблица со всеми книгами.
    Снизу — кнопки.
    """

    # Внутренние имена столбцов таблицы (для программы)
    COLUMNS = ("udc", "author", "title", "year", "copies")
    # Подписи столбцов, которые видит человек
    COLUMN_TITLES = {
        "udc": "УДК",
        "author": "Автор",
        "title": "Название",
        "year": "Год",
        "copies": "Экземпляры",
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Библиотека книг")
        self.root.geometry("980x620")
        self.root.minsize(860, 520)

        # Загружаем книги из базы и строим дерево
        self.catalog: LibraryCatalog = create_catalog()

        self._build_form()
        self._build_table()
        self._build_buttons()
        # Сразу показываем книги в таблице
        self.refresh_table_by_year()

    def _build_form(self) -> None:
        """Рисует блок с полями: УДК, автор, название, год, экземпляры."""
        frame = ttk.LabelFrame(self.root, text="Данные книги", padding=12)
        frame.pack(fill="x", padx=12, pady=(12, 6))

        labels = [
            ("Номер УДК:", "udc"),
            ("Автор (фамилия и инициалы):", "author"),
            ("Название:", "title"),
            ("Год издания:", "year"),
            ("Количество экземпляров:", "copies"),
        ]

        self.entries: dict[str, ttk.Entry] = {}
        for row, (label_text, key) in enumerate(labels):
            ttk.Label(frame, text=label_text).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=4
            )
            entry = ttk.Entry(frame, width=60)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        frame.columnconfigure(1, weight=1)

    def _build_table(self) -> None:
        """Рисует таблицу со списком книг и полосу прокрутки."""
        table_frame = ttk.LabelFrame(
            self.root, text="Книги в библиотеке (сортировка по году издания)", padding=8
        )
        table_frame.pack(fill="both", expand=True, padx=12, pady=6)

        self.table = ttk.Treeview(
            table_frame,
            columns=self.COLUMNS,
            show="headings",
            height=14,
        )

        for column in self.COLUMNS:
            self.table.heading(column, text=self.COLUMN_TITLES[column])
            width = 120 if column != "title" else 280
            self.table.column(column, width=width, anchor="center")

        self.table.column("author", width=180, anchor="w")
        self.table.column("title", anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.table.yview
        )
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Если кликнуть по строке — данные попадут в поля ввода сверху
        self.table.bind("<<TreeviewSelect>>", self._on_row_select)

    def _build_buttons(self) -> None:
        """Рисует кнопки внизу окна."""
        buttons = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Добавить книгу", command=self.add_book).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(buttons, text="Удалить книгу", command=self.delete_book).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(
            buttons, text="Отчет по годам", command=self.show_report_by_year
        ).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Очистить форму", command=self.clear_form).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(
            buttons, text="Загрузить начальные данные", command=self.reload_initial_data
        ).pack(side="left")

    def _read_form(self) -> Book | None:
        """
        Читает то, что написано в полях, и проверяет, всё ли правильно.

        Если что-то не так — показывает сообщение и возвращает None.
        """
        udc = self.entries["udc"].get().strip()
        author = self.entries["author"].get().strip()
        title = self.entries["title"].get().strip()
        year_raw = self.entries["year"].get().strip()
        copies_raw = self.entries["copies"].get().strip()

        if not all([udc, author, title, year_raw, copies_raw]):
            messagebox.showwarning(
                "Проверка данных", "Заполните все поля перед выполнением операции."
            )
            return None

        try:
            year = int(year_raw)
            copies = int(copies_raw)
        except ValueError:
            messagebox.showerror(
                "Проверка данных",
                "Год издания и количество экземпляров должны быть целыми числами.",
            )
            return None

        if year < 0:
            messagebox.showerror(
                "Проверка данных", "Год издания не может быть отрицательным."
            )
            return None

        if copies < 0:
            messagebox.showerror(
                "Проверка данных", "Количество экземпляров не может быть отрицательным."
            )
            return None

        return Book(udc=udc, author=author, title=title, year=year, copies=copies)

    def add_book(self) -> None:
        """По кнопке «Добавить книгу» — сохраняем в базу и в дерево."""
        book = self._read_form()
        if book is None:
            return

        existed = self.catalog.insert(book)
        self.refresh_table_by_year()

        if existed:
            messagebox.showinfo(
                "Добавление",
                "Книга с таким УДК уже была в каталоге. Запись обновлена в базе.",
            )
        else:
            messagebox.showinfo(
                "Добавление",
                "Книга добавлена в бинарное дерево и сохранена в SQLite.",
            )

        self.clear_form()

    def delete_book(self) -> None:
        """
        По кнопке «Удалить книгу».

        Номер УДК можно ввести вручную или выбрать книгу в таблице.
        """
        udc = self.entries["udc"].get().strip()
        if not udc:
            selected = self.table.selection()
            if selected:
                values = self.table.item(selected[0], "values")
                udc = values[0]

        if not udc:
            messagebox.showwarning(
                "Удаление",
                "Укажите номер УДК в форме или выберите строку в таблице.",
            )
            return

        if not self.catalog.delete(udc):
            messagebox.showerror(
                "Удаление", f"Книга с УДК «{udc}» не найдена в библиотеке."
            )
            return

        self.refresh_table_by_year()
        self.clear_form()
        messagebox.showinfo("Удаление", "Книга удалена из дерева и из базы SQLite.")

    def refresh_table_by_year(self) -> list[Book]:
        """
        Обновляет таблицу на экране.

        Книги идут от самого старого года к самому новому.
        Возвращает тот же список, что показан в таблице.
        """
        for item in self.table.get_children():
            self.table.delete(item)

        books = self.catalog.books_sorted_by_year()
        for book in books:
            self.table.insert("", "end", values=book.as_row())

        children = self.table.get_children()
        if children:
            self.table.selection_set(children[0])
            self.table.focus(children[0])
            self.table.see(children[0])

        return books

    def show_report_by_year(self) -> None:
        """
        По кнопке «Отчёт по годам»: заново читает базу и показывает результат.

        Раньше таблица уже была заполнена при открытии программы,
        поэтому повторное нажатие казалось «пустым» — теперь есть окно с отчётом.
        """
        self.catalog.reload_from_database()
        books = self.refresh_table_by_year()

        if not books:
            messagebox.showinfo(
                "Отчёт по годам",
                "В библиотеке пока нет ни одной книги.\n\n"
                "Добавьте книгу или нажмите «Загрузить начальные данные».",
            )
            return

        years = [book.year for book in books]
        lines = [
            f"{book.year} — «{book.title}», {book.author} (УДК {book.udc})"
            for book in books
        ]
        report_text = (
            f"Всего книг: {len(books)}\n"
            f"Самый ранний год: {min(years)}\n"
            f"Самый поздний год: {max(years)}\n\n"
            "Список по годам (от старого к новому):\n"
            + "\n".join(lines)
            + "\n\nТот же список обновлён в таблице в окне программы."
        )
        messagebox.showinfo("Отчёт по годам", report_text)

    def reload_initial_data(self) -> None:
        """По кнопке — вернуть стартовый набор книг (спросит подтверждение)."""
        if not messagebox.askyesno(
            "Начальные данные",
            "Каталог в базе будет заменён начальным набором книг. Продолжить?",
        ):
            return

        self.catalog.reset_to_initial_data()
        self.refresh_table_by_year()
        self.clear_form()

    def clear_form(self) -> None:
        """Стирает текст в полях ввода. Книги в базе не трогает."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def _on_row_select(self, _event: tk.Event) -> None:
        """Когда выбрали строку в таблице — копируем её в поля сверху."""
        selected = self.table.selection()
        if not selected:
            return

        udc, author, title, year, copies = self.table.item(selected[0], "values")
        values = {
            "udc": udc,
            "author": author,
            "title": title,
            "year": year,
            "copies": copies,
        }
        for key, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, values[key])


def run_app() -> None:
    """Создаёт окно и запускает программу, пока его не закроют."""
    root = tk.Tk()
    LibraryApp(root)
    root.mainloop()
