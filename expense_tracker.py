import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker - Личный трекер расходов")
        self.root.geometry("900x600")

        # Данные
        self.expenses = []
        self.load_data()

        # Создание интерфейса
        self.create_input_frame()
        self.create_table_frame()
        self.create_filter_frame()
        self.create_stats_frame()

        # Обновление таблицы
        self.refresh_table()

    def create_input_frame(self):
        """Форма для добавления расходов"""
        input_frame = ttk.LabelFrame(self.root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky="w", padx=5)
        self.amount_entry = ttk.Entry(input_frame, width=20)
        self.amount_entry.grid(row=0, column=1, padx=5)

        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, sticky="w", padx=5)
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", "Покупки", "Другое"]
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, values=categories, width=15)
        self.category_combo.grid(row=0, column=3, padx=5)
        self.category_combo.set("Еда")

        # Дата
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, sticky="w", padx=5)
        self.date_entry = ttk.Entry(input_frame, width=15)
        self.date_entry.grid(row=0, column=5, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Кнопка добавления
        add_btn = ttk.Button(input_frame, text="Добавить расход", command=self.add_expense)
        add_btn.grid(row=0, column=6, padx=10)

    def create_table_frame(self):
        """Таблица с расходами"""
        table_frame = ttk.LabelFrame(self.root, text="Список расходов", padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Создание таблицы
        columns = ("id", "date", "category", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Дата")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма (₽)")

        self.tree.column("id", width=50)
        self.tree.column("date", width=100)
        self.tree.column("category", width=120)
        self.tree.column("amount", width=100)

        # Скроллбар
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_filter_frame(self):
        """Фильтрация"""
        filter_frame = ttk.LabelFrame(self.root, text="Фильтрация", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Фильтр по категории
        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5)
        self.filter_category_var = tk.StringVar()
        self.filter_category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                   values=["Все"] + ["Еда", "Транспорт", "Развлечения", "Здоровье", "Покупки", "Другое"],
                                                   width=15)
        self.filter_category_combo.grid(row=0, column=1, padx=5)
        self.filter_category_combo.set("Все")

        # Фильтр по дате (начало)
        ttk.Label(filter_frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, padx=5)
        self.filter_date_from = ttk.Entry(filter_frame, width=15)
        self.filter_date_from.grid(row=0, column=3, padx=5)

        # Фильтр по дате (конец)
        ttk.Label(filter_frame, text="до:").grid(row=0, column=4, padx=5)
        self.filter_date_to = ttk.Entry(filter_frame, width=15)
        self.filter_date_to.grid(row=0, column=5, padx=5)

        # Кнопка применения фильтра
        filter_btn = ttk.Button(filter_frame, text="Применить фильтр", command=self.refresh_table)
        filter_btn.grid(row=0, column=6, padx=10)

        # Кнопка сброса фильтра
        reset_btn = ttk.Button(filter_frame, text="Сбросить фильтр", command=self.reset_filter)
        reset_btn.grid(row=0, column=7, padx=5)

    def create_stats_frame(self):
        """Статистика и подсчёт суммы за период"""
        stats_frame = ttk.LabelFrame(self.root, text="Статистика", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(stats_frame, text="Период для подсчёта (ГГГГ-ММ-ДД):").pack(side="left", padx=5)

        self.period_from = ttk.Entry(stats_frame, width=15)
        self.period_from.pack(side="left", padx=5)

        ttk.Label(stats_frame, text="-").pack(side="left")

        self.period_to = ttk.Entry(stats_frame, width=15)
        self.period_to.pack(side="left", padx=5)

        calc_btn = ttk.Button(stats_frame, text="Подсчитать сумму", command=self.calculate_sum_period)
        calc_btn.pack(side="left", padx=10)

        self.sum_label = ttk.Label(stats_frame, text="Сумма за период: 0.00 ₽", font=("Arial", 10, "bold"))
        self.sum_label.pack(side="left", padx=20)

    def validate_amount(self, amount_str):
        """Проверка суммы"""
        try:
            amount = float(amount_str)
            if amount <= 0:
                return False, "Сумма должна быть положительным числом"
            return True, amount
        except ValueError:
            return False, "Сумма должна быть числом"

    def validate_date(self, date_str):
        """Проверка формата даты"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def add_expense(self):
        """Добавление расхода"""
        amount_str = self.amount_entry.get().strip()
        category = self.category_var.get()
        date_str = self.date_entry.get().strip()

        # Валидация
        is_valid_amount, amount_or_error = self.validate_amount(amount_str)
        if not is_valid_amount:
            messagebox.showerror("Ошибка", amount_or_error)
            return

        if not self.validate_date(date_str):
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return

        # Добавление
        expense = {
            "id": len(self.expenses) + 1,
            "amount": amount_or_error,
            "category": category,
            "date": date_str
        }
        self.expenses.append(expense)
        self.save_data()

        # Очистка полей
        self.amount_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.refresh_table()
        messagebox.showinfo("Успех", "Расход добавлен!")

    def refresh_table(self):
        """Обновление таблицы с учётом фильтров"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получение фильтров
        category_filter = self.filter_category_var.get()
        date_from = self.filter_date_from.get().strip()
        date_to = self.filter_date_to.get().strip()

        # Фильтрация
        filtered_expenses = self.expenses

        if category_filter != "Все":
            filtered_expenses = [e for e in filtered_expenses if e["category"] == category_filter]

        if date_from:
            filtered_expenses = [e for e in filtered_expenses if e["date"] >= date_from]

        if date_to:
            filtered_expenses = [e for e in filtered_expenses if e["date"] <= date_to]

        # Отображение
        for expense in filtered_expenses:
            self.tree.insert("", "end", values=(
                expense["id"],
                expense["date"],
                expense["category"],
                f"{expense['amount']:.2f}"
            ))

    def reset_filter(self):
        """Сброс фильтров"""
        self.filter_category_combo.set("Все")
        self.filter_date_from.delete(0, tk.END)
        self.filter_date_to.delete(0, tk.END)
        self.refresh_table()

    def calculate_sum_period(self):
        """Подсчёт суммы расходов за выбранный период"""
        date_from = self.period_from.get().strip()
        date_to = self.period_to.get().strip()

        if not date_from or not date_to:
            messagebox.showwarning("Предупреждение", "Введите обе даты для периода")
            return

        if not self.validate_date(date_from) or not self.validate_date(date_to):
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return

        if date_from > date_to:
            messagebox.showerror("Ошибка", "Дата начала не может быть позже даты окончания")
            return

        total = 0
        for expense in self.expenses:
            if date_from <= expense["date"] <= date_to:
                total += expense["amount"]

        self.sum_label.config(text=f"Сумма за период: {total:.2f} ₽")
        messagebox.showinfo("Результат", f"Общая сумма расходов с {date_from} по {date_to}: {total:.2f} ₽")

    def load_data(self):
        """Загрузка данных из JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
            except:
                self.expenses = []
        else:
            self.expenses = []

    def save_data(self):
        """Сохранение данных в JSON"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.expenses, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
