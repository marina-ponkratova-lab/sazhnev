import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os

# --- 1. Конфигурация и работа с данными (JSON) ---
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "favorites.json")
GITHUB_API_URL = "https://api.github.com/search/users"

def ensure_data_dir_exists():
    """Создает каталог 'data', если его нет на диске."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        # Создаем пустой файл для избранного, чтобы избежать ошибок при чтении
        with open(DATA_FILE, "w") as f:
            json.dump([], f)

def load_favorites():
    """Загружает избранных пользователей из файла JSON."""
    ensure_data_dir_exists()
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_favorites(favorites_list):
    """Сохраняет список избранных пользователей в файл JSON."""
    ensure_data_dir_exists()
    with open(DATA_FILE, "w") as file:
        json.dump(favorites_list, file, indent=4)


# --- 2. Логика работы с API ---
def search_github_users(query):
    """
    Выполняет поиск пользователей через GitHub API.
    Возвращает список словарей с данными о пользователях.
    """
    try:
        params = {"q": query}
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(GITHUB_API_URL, params=params, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP (404, 500)
        
        data = response.json()
        return [
            {
                "login": item["login"],
                "id": item["id"],
                "html_url": item["html_url"],
                "avatar_url": item["avatar_url"],
            }
            for item in data.get("items", [])
        ]
    except requests.exceptions.RequestException as e:
        messagebox.showerror(
            "Ошибка сети", f"Не удалось подключиться к GitHub:\n{str(e)}"
        )
        return []


# --- 3. Логика GUI ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GitHub User Finder")
        self.geometry("900x600")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        
        self.favorites = load_favorites()
        
        self.create_widgets()
        self.update_favs_list() # Обновляем избранное при запуске

    def create_widgets(self):
        # --- Верхний фрейм: Поиск ---
        frame_search = tk.Frame(self, bg="#f0f0f0")
        frame_search.pack(pady=15, fill="x", padx=20)

        tk.Label(frame_search, text="Поиск:", font=("Arial", 12), bg="#f0f0f0").pack(
            side="left"
        )
        self.entry_search = tk.Entry(frame_search, font=("Arial", 12), width=30)
        self.entry_search.pack(side="left", ipadx=5, ipady=3)
        self.entry_search.focus_set() # Ставим курсор в поле при запуске

        btn_search = tk.Button(
            frame_search,
            text="Найти",
            command=self.on_search,
            bg="#4CAF50",
            fg="white",
            width=10,
        )
        btn_search.pack(side="left", padx=10)

        # --- Основной фрейм: Результаты и Избранное ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#e0e0e0", sashwidth=5)
        main_pane.pack(padx=20, pady=10, fill="both", expand=True)

        # Левая часть: Результаты поиска (Treeview)
        frame_results = tk.Frame(main_pane, bg="white")
        
        # Treeview для отображения списка с аватарами и кнопками
        self.tree = ttk.Treeview(
            frame_results,
            columns=("login", "url"),
            show="headings",
            height=25,
        )
        self.tree.heading("login", text="Логин")
        self.tree.heading("url", text="Профиль")
        self.tree.column("login", width=250)
        self.tree.column("url", width=0)  # Скрываем колонку с URL

        style = ttk.Style(self)
        style.configure("Treeview", rowheight=40) 

        self.tree.pack(fill="both", expand=True)
        
        main_pane.add(frame_results)

        # Правая часть: Избранное (Listbox)
        frame_favs = tk.Frame(main_pane, bg="white")
        
        tk.Label(frame_favs, text="Избранное:", font=("Arial", 12)).pack(pady=5)
        
        self.listbox_favs = tk.Listbox(frame_favs, font=("Arial", 11), height=25)
        self.listbox_favs.pack(fill="both", expand=True)
        
        main_pane.add(frame_favs)

    def on_search(self):
        """Обработчик нажатия кнопки 'Найти'."""
        query = self.entry_search.get().strip()

        # --- Валидация ввода ---
        if not query:
            messagebox.showwarning("Ошибка", "Поле поиска не должно быть пустым!")
            return

        users = search_github_users(query)

        # Очищаем дерево перед вставкой новых данных
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        if not users:
            messagebox.showinfo("Результат", "Пользователи не найдены.")
            return

        for user in users:
            # Вставляем строку. Значение 'url' нужно для открытия профиля.
            self.tree.insert(
                "",
                "end",
                values=(user["login"], user["html_url"]),
                tags=(user["id"],),
            )
        
    def add_to_favs(self, user_id):
        """Добавляет пользователя в избранное по его ID."""
        # Находим пользователя в дереве по ID и добавляем в список избранного
        for child in self.tree.get_children():
            if str(self.tree.item(child)["tags"][0]) == str(user_id):
                login = self.tree.item(child)["values"][0]
                url = self.tree.item(child)["values"][1]
                
                user_data = {"login": login, "html_url": url}
                
                if user_data not in self.favorites:
                    self.favorites.append(user_data)
                    save_favorites(self.favorites)
                    messagebox.showinfo("Успех", f"Пользователь {login} добавлен в избранное.")
                    self.update_favs_list()
                else:
                    messagebox.showwarning("Дубликат", "Пользователь уже в избранном.")
                break

    def update_favs_list(self):
        """Обновляет виджет Listbox с избранными пользователями."""
        self.listbox_favs.delete(0, tk.END) # Очищаем список перед обновлением
        
        if not self.favorites:
            return
            
        for fav in self.favorites:
            # Вставляем в Listbox только логин для компактности
            self.listbox_favs.insert(tk.END, fav["login"])


# --- 4. Точка входа ---
if __name__ == '__main__':
    app = App()
    app.mainloop()
