import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import datetime
import hashlib


class OnlineStoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Интернет-магазин - Администрирование")
        self.root.geometry("1200x800")

        # Подключение к базе данных SQLite
        self.conn = sqlite3.connect('online_store.db')
        self.cursor = self.conn.cursor()

        # Создание таблиц, если они не существуют
        self.create_tables()

        # Основные цвета
        self.bg_color = "#F0F0F0"
        self.button_color = "#4CAF50"
        self.button_color_alt = "#45a049"
        self.text_color = "#333333"

        # Отображение главного меню
        self.show_main_menu()

    def create_tables(self):
        """Создание таблиц, если они не существуют"""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );

            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                parent_category_id INTEGER,
                FOREIGN KEY (parent_category_id) REFERENCES categories(category_id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_method TEXT,
                payment_status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS tags (
                tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS product_tags (
                product_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (product_id, tag_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS product_reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                review_text TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def show_main_menu(self):
        """Отображение главного меню с кнопками для таблиц"""
        self.clear_window()

        title_label = tk.Label(self.root, text="Администрирование интернет-магазина",
                               font=("Arial", 20, "bold"), fg=self.text_color)
        title_label.pack(pady=20)

        # Создаем фрейм для кнопок
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(expand=True)

        # Кнопки для каждой таблицы
        buttons = [
            ("Пользователи", self.show_users),
            ("Категории", self.show_categories),
            ("Товары", self.show_products),
            ("Заказы", self.show_orders),
            ("Элементы заказов", self.show_order_items),
            ("Теги", self.show_tags),
            ("Теги товаров", self.show_product_tags),
            ("Отзывы", self.show_reviews)
        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command,
                            bg=self.button_color, fg="white", font=("Arial", 12),
                            width=25, height=2, bd=0)
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)

        # Кнопка выхода
        exit_btn = tk.Button(self.root, text="Выход", command=self.root.quit,
                             bg="#f44336", fg="white", font=("Arial", 12),
                             width=15, height=1, bd=0)
        exit_btn.pack(pady=20)

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_table_view(self, title, table_name, columns, id_column, search_columns=None):
        """Общий метод для отображения таблицы"""
        self.clear_window()

        # Заголовок
        tk.Label(self.root, text=title, font=("Arial", 16, "bold"),
                 fg=self.text_color).pack(pady=10)

        # Фрейм для поиска
        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        if search_columns:
            self.search_entry = tk.Entry(search_frame, font=("Arial", 12))
            self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            search_btn = tk.Button(search_frame, text="Поиск",
                                   command=lambda: self.search_table(table_name, columns, id_column, search_columns),
                                   bg=self.button_color, fg="white")
            search_btn.pack(side=tk.LEFT, padx=5)

            reset_btn = tk.Button(search_frame, text="Сброс",
                                  command=lambda: self.display_table(table_name, columns, id_column),
                                  bg=self.button_color_alt, fg="white")
            reset_btn.pack(side=tk.LEFT, padx=5)

        # Таблица с данными
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        # Кнопки CRUD
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        add_btn = tk.Button(button_frame, text="Добавить",
                            command=lambda: self.show_add_form(table_name, columns, id_column),
                            bg=self.button_color, fg="white")
        add_btn.pack(side=tk.LEFT, padx=5)

        edit_btn = tk.Button(button_frame, text="Изменить",
                             command=lambda: self.show_edit_form(table_name, columns, id_column),
                             bg=self.button_color_alt, fg="white")
        edit_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(button_frame, text="Удалить",
                               command=lambda: self.delete_record(table_name, id_column),
                               bg="#f44336", fg="white")
        delete_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(button_frame, text="Назад",
                             command=self.show_main_menu,
                             bg="#607d8b", fg="white")
        back_btn.pack(side=tk.RIGHT, padx=5)

        # Отображение данных
        self.display_table(table_name, columns, id_column)

    def display_table(self, table_name, columns, id_column):
        """Отображение данных таблицы"""
        try:
            # Очистка таблицы
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Получение данных
            self.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.cursor.fetchall()

            # Заполнение таблицы
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")

    def search_table(self, table_name, columns, id_column, search_columns):
        """Поиск по таблице"""
        search_term = self.search_entry.get()
        if not search_term:
            self.display_table(table_name, columns, id_column)
            return

        try:
            # Очистка таблицы
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Создание условий поиска
            conditions = " OR ".join([f"{col} LIKE ?" for col in search_columns])
            params = [f"%{search_term}%"] * len(search_columns)

            # Выполнение поиска
            query = f"SELECT * FROM {table_name} WHERE {conditions}"
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            # Заполнение результатов
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")

    def show_add_form(self, table_name, columns, id_column):
        """Форма для добавления записи"""
        form = tk.Toplevel(self.root)
        form.title(f"Добавить запись в {table_name}")
        form.geometry("500x600")

        self.current_form = form
        self.current_table = table_name
        self.current_columns = columns
        self.current_id_column = id_column

        # Определяем, какие поля нужно показывать
        fields_to_show = []
        if table_name == "users":
            fields_to_show = ["username", "email", "password_hash", "first_name", "last_name", "phone", "is_active"]
        elif table_name == "categories":
            fields_to_show = ["name", "description"]
        elif table_name == "products":
            fields_to_show = ["category_id", "name", "description", "price", "stock_quantity", "is_active"]
        elif table_name == "orders":
            fields_to_show = ["user_id", "status", "total_amount", "shipping_address", "payment_method",
                              "payment_status"]
        elif table_name == "order_items":
            fields_to_show = ["order_id", "product_id", "quantity", "unit_price"]
        elif table_name == "tags":
            fields_to_show = ["name", "description"]
        elif table_name == "product_tags":
            fields_to_show = ["product_id", "tag_id"]
        elif table_name == "product_reviews":
            fields_to_show = ["product_id", "user_id", "rating", "review_text"]

        # Создание полей формы
        self.form_entries = {}
        for i, col in enumerate(fields_to_show):
            tk.Label(form, text=f"{col}:").grid(row=i, column=0, padx=10, pady=5, sticky=tk.E)

            # Специальные обработчики для разных типов полей
            if table_name == "products" and col == "category_id":
                # Выпадающий список для категорий
                self.cursor.execute("SELECT category_id, name FROM categories")
                categories = self.cursor.fetchall()
                category_names = [f"{cat[0]} - {cat[1]}" for cat in categories]
                category_var = tk.StringVar(form)
                dropdown = ttk.Combobox(form, textvariable=category_var, values=category_names)
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            elif table_name == "orders" and col == "status":
                # Выпадающий список для статуса заказа
                status_var = tk.StringVar(form)
                dropdown = ttk.Combobox(form, textvariable=status_var,
                                        values=["pending", "processing", "shipped", "delivered", "cancelled"])
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            elif col == "is_active":
                # Чекбокс для булевых значений
                var = tk.BooleanVar(value=True)
                checkbox = tk.Checkbutton(form, variable=var)
                checkbox.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = var
            elif col == "rating":
                # Выпадающий список для рейтинга
                rating_var = tk.StringVar(form)
                dropdown = ttk.Combobox(form, textvariable=rating_var, values=[1, 2, 3, 4, 5])
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            else:
                # Обычное текстовое поле
                entry = tk.Entry(form)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = entry

        # Кнопки
        button_frame = tk.Frame(form)
        button_frame.grid(row=len(fields_to_show) + 1, column=0, columnspan=2, pady=10)

        save_btn = tk.Button(button_frame, text="Сохранить", command=lambda: self.save_record(fields_to_show))
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(button_frame, text="Отмена", command=form.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def show_edit_form(self, table_name, columns, id_column):
        """Форма для редактирования записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для редактирования")
            return

        record_id = self.tree.item(selected[0])['values'][0]

        form = tk.Toplevel(self.root)
        form.title(f"Редактировать запись в {table_name}")
        form.geometry("500x600")

        self.current_form = form
        self.current_table = table_name
        self.current_columns = columns
        self.current_id_column = id_column
        self.current_record_id = record_id

        # Определяем, какие поля нужно показывать (аналогично show_add_form)
        fields_to_show = []
        if table_name == "users":
            fields_to_show = ["username", "email", "password_hash", "first_name", "last_name", "phone", "is_active"]
        elif table_name == "categories":
            fields_to_show = ["name", "description", "parent_category_id"]
        elif table_name == "products":
            fields_to_show = ["category_id", "name", "description", "price", "stock_quantity", "is_active"]
        elif table_name == "orders":
            fields_to_show = ["user_id", "status", "total_amount", "shipping_address", "payment_method",
                              "payment_status"]
        elif table_name == "order_items":
            fields_to_show = ["order_id", "product_id", "quantity", "unit_price"]
        elif table_name == "tags":
            fields_to_show = ["name", "description"]
        elif table_name == "product_tags":
            fields_to_show = ["product_id", "tag_id"]
        elif table_name == "product_reviews":
            fields_to_show = ["product_id", "user_id", "rating", "review_text"]

        # Получение данных записи
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = ?", (record_id,))
        record = self.cursor.fetchone()

        # Создаем словарь для удобного доступа к значениям полей
        record_dict = dict(zip([col[0] for col in self.cursor.description], record))

        # Создание полей формы
        self.form_entries = {}
        for i, col in enumerate(fields_to_show):
            tk.Label(form, text=f"{col}:").grid(row=i, column=0, padx=10, pady=5, sticky=tk.E)

            # Получаем текущее значение поля
            current_value = record_dict.get(col, "")

            # Для пароля показываем звездочки
            if col == "password_hash":
                current_value = "********"

            # Специальные обработчики для разных типов полей
            if table_name == "products" and col == "category_id":
                # Выпадающий список для категорий
                self.cursor.execute("SELECT category_id, name FROM categories")
                categories = self.cursor.fetchall()
                category_names = [f"{cat[0]} - {cat[1]}" for cat in categories]
                category_var = tk.StringVar(form)

                # Установка текущего значения
                current_cat_id = current_value
                self.cursor.execute("SELECT name FROM categories WHERE category_id = ?", (current_cat_id,))
                current_cat_name = self.cursor.fetchone()[0]
                category_var.set(f"{current_cat_id} - {current_cat_name}")

                dropdown = ttk.Combobox(form, textvariable=category_var, values=category_names)
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            elif table_name == "orders" and col == "status":
                # Выпадающий список для статуса заказа
                status_var = tk.StringVar(form, value=current_value)
                dropdown = ttk.Combobox(form, textvariable=status_var,
                                        values=["pending", "processing", "shipped", "delivered", "cancelled"])
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            elif col == "is_active":
                # Чекбокс для булевых значений
                var = tk.BooleanVar(value=bool(current_value))
                checkbox = tk.Checkbutton(form, variable=var)
                checkbox.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = var
            elif col == "rating":
                # Выпадающий список для рейтинга
                rating_var = tk.StringVar(form, value=current_value)
                dropdown = ttk.Combobox(form, textvariable=rating_var, values=[1, 2, 3, 4, 5])
                dropdown.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = dropdown
            else:
                # Обычное текстовое поле
                entry = tk.Entry(form)
                entry.insert(0, str(current_value))
                entry.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                self.form_entries[col] = entry

        # Кнопки
        button_frame = tk.Frame(form)
        button_frame.grid(row=len(fields_to_show) + 1, column=0, columnspan=2, pady=10)

        save_btn = tk.Button(button_frame, text="Сохранить", command=lambda: self.update_record(fields_to_show))
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(button_frame, text="Отмена", command=form.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def save_record(self, fields_to_show):
        """Сохранение новой записи"""
        try:
            columns = []
            placeholders = []
            values = []

            for col in fields_to_show:
                widget = self.form_entries[col]

                if isinstance(widget, ttk.Combobox):
                    value = widget.get()
                    if col == "category_id":
                        value = value.split(" - ")[0]
                elif isinstance(widget, tk.BooleanVar):
                    value = 1 if widget.get() else 0
                else:
                    value = widget.get()

                # Хеширование пароля, если это поле password_hash
                if col == "password_hash":
                    value = self.hash_password(value)

                # Проверка обязательных полей
                if (self.current_table == "users" and col in ["username", "email", "password_hash"] and not value):
                    messagebox.showerror("Ошибка", f"Поле {col} обязательно для заполнения")
                    return
                if (self.current_table == "products" and col in ["name", "price", "category_id"] and not value):
                    messagebox.showerror("Ошибка", f"Поле {col} обязательно для заполнения")
                    return

                columns.append(col)
                placeholders.append("?")
                values.append(value)

            # Создание SQL запроса
            query = f"INSERT INTO {self.current_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

            self.cursor.execute(query, values)
            self.conn.commit()

            messagebox.showinfo("Успех", "Запись успешно добавлена")
            self.current_form.destroy()

            # Обновляем отображение таблицы
            if hasattr(self, 'tree'):
                self.display_table(self.current_table, self.current_columns, self.current_id_column)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить запись: {e}")
            print(f"Ошибка SQL: {e}")

    def hash_password(self, password):
        """Хеширование пароля с использованием SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def update_record(self, fields_to_show):
        """Обновление существующей записи"""
        try:
            updates = []
            values = []

            for col in fields_to_show:
                widget = self.form_entries[col]

                if isinstance(widget, ttk.Combobox):
                    value = widget.get()
                    if col == "category_id":
                        value = value.split(" - ")[0]
                elif isinstance(widget, tk.BooleanVar):
                    value = 1 if widget.get() else 0
                else:
                    value = widget.get()

                # Хеширование пароля, если это поле password_hash и оно было изменено
                if col == "password_hash" and value != "********":
                    value = self.hash_password(value)

                updates.append(f"{col} = ?")
                values.append(value)

            # Добавляем ID записи в конец для WHERE
            values.append(self.current_record_id)

            # Создание SQL запроса
            updates_str = ", ".join(updates)
            query = f"UPDATE {self.current_table} SET {updates_str} WHERE {self.current_id_column} = ?"

            self.cursor.execute(query, values)
            self.conn.commit()

            messagebox.showinfo("Успех", "Запись успешно обновлена")
            self.current_form.destroy()

            # Обновляем отображение таблицы
            if hasattr(self, 'tree'):
                self.display_table(self.current_table, self.current_columns, self.current_id_column)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить запись: {e}")

    def delete_record(self, table_name, id_column):
        """Удаление записи"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return

        record_id = self.tree.item(selected[0])['values'][0]

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту запись?"):
            try:
                self.cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = ?", (record_id,))
                self.conn.commit()

                messagebox.showinfo("Успех", "Запись успешно удалена")
                self.display_table(table_name, self.current_columns, id_column)
            except sqlite3.Error as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить запись: {e}")

    # Методы для отображения конкретных таблиц
    def show_users(self):
        """Отображение таблицы пользователей с фиктивным паролем"""
        # Указываем только нужные столбцы для отображения
        display_columns = (
        "ID пользователя", "Ник", "email", "Пароль", "Имя", "Фамилия", "Телефон", "Дата регистрации", "Активен")
        db_columns = ["user_id", "username", "email", "password_hash", "first_name", "last_name", "phone", "registration_date",
                      "is_active"]

        # Очищаем текущее отображение
        self.clear_window()

        # Заголовок
        tk.Label(self.root, text="Пользователи", font=("Arial", 16, "bold"),
                 fg=self.text_color).pack(pady=10)

        # Таблица с данными
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(table_frame, columns=display_columns, show='headings',
                                 yscrollcommand=scroll_y.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        scroll_y.config(command=self.tree.yview)

        # Настраиваем заголовки столбцов
        for col in display_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)

        # Получаем данные из БД
        self.cursor.execute(f"SELECT {', '.join(db_columns)} FROM users")
        rows = self.cursor.fetchall()

        # Заполняем таблицу данными, добавляя фиктивный пароль
        for row in rows:
            # Добавляем звездочки вместо пароля (4-я позиция)
            row_with_password = row[:2] + ("********",) + row[2:]
            self.tree.insert('', tk.END, values=row_with_password)

        # Остальной код (поиск, кнопки) остается без изменений
        search_frame = tk.Frame(self.root, bg=self.bg_color)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        self.search_entry = tk.Entry(search_frame, font=("Arial", 12))
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        search_btn = tk.Button(search_frame, text="Поиск",
                               command=lambda: self.search_users(),
                               bg=self.button_color, fg="white")
        search_btn.pack(side=tk.LEFT, padx=5)

        reset_btn = tk.Button(search_frame, text="Сброс",
                              command=lambda: self.show_users(),
                              bg=self.button_color_alt, fg="white")
        reset_btn.pack(side=tk.LEFT, padx=5)

        # Кнопки управления
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(button_frame, text="Добавить",
                  command=lambda: self.show_add_form("users", db_columns, "user_id"),
                  bg=self.button_color, fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Изменить",
                  command=lambda: self.show_edit_form("users", db_columns, "user_id"),
                  bg=self.button_color_alt, fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Удалить", command=lambda: self.delete_record("users", "user_id"),
                  bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Назад", command=self.show_main_menu,
                  bg="#607d8b", fg="white").pack(side=tk.RIGHT, padx=5)

    def search_users(self):
        """Поиск пользователей"""
        search_term = self.search_entry.get()
        if not search_term:
            self.show_users()
            return

        try:
            # Очистка таблицы
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Поиск по username, email, first_name и last_name
            query = """
            SELECT user_id, username, email, first_name, last_name, phone, registration_date, is_active 
            FROM users 
            WHERE username LIKE ? OR email LIKE ? OR first_name LIKE ? OR last_name LIKE ?
            """
            params = [f"%{search_term}%"] * 4

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            # Заполнение результатов
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")

    def show_categories(self):
        """Отображение таблицы категорий"""
        columns = ("ID Категории", "Название", "Описание")
        self.show_table_view("Категории", "categories", columns, "category_id", ["name"])

    def show_products(self):
        """Отображение таблицы товаров"""
        columns = (
        "ID Продукта", "ID Категории", "Название", "Описание", "Цена", "В наличии", "Дата добавления", "Продается")
        self.show_table_view("Товары", "products", columns, "product_id", ["name", "description"])

    def show_orders(self):
        """Отображение таблицы заказов"""
        columns = ("ID Заказа", "ID Пользователя", "Дата", "Статус", "Всего к оплате", "Адрес отправления", "Способ оплаты")
        self.show_table_view("Заказы", "orders", columns, "order_id", ["status"])

    def show_order_items(self):
        """Отображение таблицы элементов заказов"""
        columns = ("ID Элемента заказа", "ID Заказа", "ID Продукта", "Колличество", "Цена за шт")
        self.show_table_view("Элементы заказов", "order_items", columns, "order_item_id")

    def show_tags(self):
        """Отображение таблицы тегов"""
        columns = ("ID Тега", "Название", "Описание")
        self.show_table_view("Теги", "tags", columns, "tag_id", ["name"])

    def show_product_tags(self):
        """Отображение таблицы тегов товаров"""
        columns = ("ID Продукта", "ID Тега")
        self.show_table_view("Теги товаров", "product_tags", columns, "product_id")

    def show_reviews(self):
        """Отображение таблицы отзывов"""
        columns = ("ID Отзыва", "ID Продукта", "ID Пользователя", "Рейтинг", "Текст", "Дата написания")
        self.show_table_view("Отзывы", "product_reviews", columns, "review_id", ["review_text"])


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = OnlineStoreApp(root)
    root.mainloop()