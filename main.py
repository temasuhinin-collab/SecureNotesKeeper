import os
import json
import base64
import tkinter.messagebox as messagebox
import customtkinter as ctk
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

# === Настройки ===
DATA_FILE = "data.enc"
KEY_FILE = "keyfile.key"
APP_TITLE = "Secure Notes & Passwords"
AUTHOR = "Artem Sukhinin"
AUTHOR_LINK = "t.me/artem_sukhinin"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.master_key = None
        self.fernet = None
        self.data = {"passwords": {}, "notes": {}}

        self.create_widgets()
        self.check_first_launch()

    def check_first_launch(self):
        if not os.path.exists(KEY_FILE):
            self.show_set_password_window()
        else:
            self.show_login_window()

    def show_set_password_window(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self)
        self.current_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.current_frame, text="Установите мастер-пароль", font=("Arial", 24, "bold")).pack(pady=10)
        ctk.CTkLabel(self.current_frame, text="Он понадобится для входа в приложение").pack(pady=5)
        
        self.pw_entry1 = ctk.CTkEntry(self.current_frame, show="*", width=300)
        self.pw_entry1.pack(pady=10)
        self.pw_entry2 = ctk.CTkEntry(self.current_frame, show="*", width=300)
        self.pw_entry2.pack(pady=10)

        ctk.CTkButton(self.current_frame, text="Создать", command=self.set_master_password).pack(pady=20)

    def show_login_window(self):
        self.clear_frame()
        self.current_frame = ctk.CTkFrame(self)
        self.current_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.current_frame, text="Введите мастер-пароль", font=("Arial", 24, "bold")).pack(pady=10)
        
        self.login_entry = ctk.CTkEntry(self.current_frame, show="*", width=300)
        self.login_entry.pack(pady=10)

        ctk.CTkButton(self.current_frame, text="Войти", command=self.login).pack(pady=20)

    def clear_frame(self):
        if hasattr(self, 'current_frame'):
            self.current_frame.destroy()

    def set_master_password(self):
        pw1 = self.pw_entry1.get()
        pw2 = self.pw_entry2.get()
        if pw1 != pw2 or not pw1:
            messagebox.showerror("Ошибка", "Пароли не совпадают или пустые")
            return

        # Генерируем пару RSA ключей
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # Шифруем приватный ключ введенным паролем
        encrypted_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(pw1.encode())
        )

        with open(KEY_FILE, "wb") as f:
            f.write(encrypted_private_key)

        self.load_data()

    def login(self):
        password = self.login_entry.get()
        if not password:
            return
        
        try:
            with open(KEY_FILE, "rb") as f:
                encrypted_private_key = f.read()
            
            private_key = serialization.load_pem_private_key(
                encrypted_private_key,
                password=password.encode(),
                backend=default_backend()
            )
            
            # Если пароль подошел и ключ расшифровался — загружаем данные
            self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", "Неверный мастер-пароль")

    def load_data(self):
        self.clear_frame()
        self.master_frame = ctk.CTkFrame(self)
        self.master_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель навигации
        nav_frame = ctk.CTkFrame(self.master_frame)
        nav_frame.pack(side="left", fill="y", padx=(0, 10))
        
        ctk.CTkButton(nav_frame, text="🔑 Пароли", command=lambda: self.show_section("passwords")).pack(fill="x", pady=5)
        ctk.CTkButton(nav_frame, text="📝 Заметки", command=lambda: self.show_section("notes")).pack(fill="x", pady=5)
        
        # Ссылка на автора
        author_label = ctk.CTkLabel(self.master_frame, text=f"by {AUTHOR}", text_color="gray", cursor="hand2")
        author_label.pack(side="bottom", pady=5)
        author_label.bind("<Button-1>", lambda e: self.open_link(AUTHOR_LINK))

        # Контент
        self.content_frame = ctk.CTkFrame(self.master_frame)
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.show_section("passwords")

        # Загрузка данных с диска
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as f:
                try:
                    self.data = json.loads(f.read().decode('utf-8'))
                except Exception:
                    self.data = {"passwords": {}, "notes": {}}

    def open_link(self, link):
        import webbrowser
        webbrowser.open(link)

    def show_section(self, section_type):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.content_frame, text="Пароли" if section_type == "passwords" else "Заметки", font=("Arial", 20, "bold")).pack(pady=10)

        listbox = ctk.CTkScrollableFrame(self.content_frame)
        listbox.pack(fill="both", expand=True, padx=10)

        items = self.data[section_type]
        for name in items.keys():
            item_frame = ctk.CTkFrame(listbox)
            item_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(item_frame, text=name, width=200, anchor="w").pack(side="left")
            
            if section_type == "passwords":
                # В паролях показываем только логин
                ctk.CTkLabel(item_frame, text=self.data[section_type][name].get("login", ""), width=150, anchor="w").pack(side="left", padx=5)
            
            ctk.CTkButton(item_frame, text="✏️", width=40, command=lambda n=name, t=section_type: self.edit_item(n, t)).pack(side="right")
            ctk.CTkButton(item_frame, text="🗑️", width=40, fg_color="red", command=lambda n=name, t=section_type: self.delete_item(n, t)).pack(side="right", padx=5)

        ctk.CTkButton(self.content_frame, text="➕ Добавить", command=lambda t=section_type: self.add_item(t)).pack(pady=10)

    def add_item(self, section_type):
        self.open_edit_window("", "", "", section_type)

    def edit_item(self, name, section_type):
        if section_type == "passwords":
            login = self.data[section_type][name].get("login", "")
            pw = self.data[section_type][name].get("password", "")
            self.open_edit_window(name, login, pw, section_type)
        else:
            text = self.data[section_type][name]
            self.open_edit_window(name, text=text, section_type=section_type)

    def open_edit_window(self, name="", login="", password="", text="", section_type="passwords"):
        edit_win = ctk.CTkToplevel(self)
        edit_win.title("Редактирование")
        edit_win.geometry("400x350")

        ctk.CTkLabel(edit_win, text="Название (имя сайта/заметки):").pack(pady=5)
        name_entry = ctk.CTkEntry(edit_win)
        name_entry.insert(0, name)
        name_entry.pack(pady=5)

        if section_type == "passwords":
            ctk.CTkLabel(edit_win, text="Логин:").pack(pady=5)
            login_entry = ctk.CTkEntry(edit_win)
            login_entry.insert(0, login)
            login_entry.pack(pady=5)

            ctk.CTkLabel(edit_win, text="Пароль:").pack(pady=5)
            pw_entry = ctk.CTkEntry(edit_win, show="*")
            pw_entry.insert(0, password)
            pw_entry.pack(pady=5)
        
            def save():
                n = name_entry.get().strip()
                l = login_entry.get().strip()
                p = pw_entry.get().strip()
                if not n:
                    messagebox.showwarning("Внимание", "Введите название")
                    return
                self.data["passwords"][n] = {"login": l, "password": p}
                self.save_data()
                edit_win.destroy()
                self.show_section("passwords")
        
            ctk.CTkButton(edit_win, text="Сохранить", command=save).pack(pady=15)

        else:
            ctk.CTkLabel(edit_win, text="Текст заметки:").pack(pady=5)
            textbox = ctk.CTkTextbox(edit_win, width=360, height=150)
            textbox.pack(pady=5)
            textbox.insert("0.0", text)

            def save():
                n = name_entry.get().strip()
                t = textbox.get("0.0", "end").strip()
                if not n:
                    messagebox.showwarning("Внимание", "Введите название")
                    return
                self.data["notes"][n] = t
                self.save_data()
                edit_win.destroy()
                self.show_section("notes")
            
            ctk.CTkButton(edit_win, text="Сохранить", command=save).pack(pady=15)

    def delete_item(self, name, section_type):
        if messagebox.askyesno("Подтверждение", f"Удалить '{name}'?"):
            if name in self.data[section_type]:
                del self.data[section_type][name]
                self.save_data()
                self.show_section(section_type)

    def save_data(self):
        # В данном упрощенном примере данные хранятся в JSON. 
        # Для промышленного использования их следует шифровать симметричным ключом.
        # Симметричный ключ можно зашифровать публичным ключом из KEY_FILE.
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    app = App()
    app.mainloop()
