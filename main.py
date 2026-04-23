import os
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image
import database
from authentication import verify_key, store_key
import passforge

# Initialize the window theme
ctk.set_appearance_mode("light") 
ctk.set_default_color_theme("blue")

class SecVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SecVault")
        self.geometry("1100x700")
        
        icon_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        try:
            self.after(200, lambda: self._apply_icon(icon_path))
        except Exception as e:
            print(f"Icon Error: {e}")

    def _apply_icon(self, path):
        img = tk.PhotoImage(file=path)
        self.iconphoto(False, img)
        
        self.db_conn = None
        self.current_user_key = None

        self.main_container = ctk.CTkFrame(self, fg_color="#E0F4FF")
        self.main_container.pack(fill="both", expand=True)

        # FIX: Instead of show_lock_window, we check if we need to setup first
        self.check_initial_state()
    
    def check_initial_state(self):
        auth_file = Path("auth_store.json")
        if not auth_file.exists() or auth_file.stat().st_size == 0:
            self.show_first_time_setup()
        else:
            self.show_lock_window()

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- SETUP SCREEN (For New Users) ---
    def show_first_time_setup(self):
        self.clear_screen()

        logo_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        logo_raw = Image.open(logo_path)
        logo_img = ctk.CTkImage(light_image=logo_raw, dark_image=logo_raw, size=(100, 100))

        outside_logo = ctk.CTkLabel(self.main_container, image=logo_img, text="")
        
        outside_logo.place(relx=0.5, rely=0.19, anchor="center")

        setup_frame = ctk.CTkFrame(self.main_container, fg_color="#CDEBFF", corner_radius=20, width=500, height=350)
        setup_frame.pack_propagate(False)
        setup_frame.place(relx=0.5, rely=0.55, anchor="center")

        ctk.CTkLabel(setup_frame, text="Set Up Master Password", font=("Helvetica", 24, "bold")).pack(pady=20)
        
        self.new_pw = ctk.CTkEntry(setup_frame, placeholder_text="Make Password", show="*", width=300)
        self.new_pw.pack(pady=10)
        
        self.confirm_pw = ctk.CTkEntry(setup_frame, placeholder_text="Confirm Password", show="*", width=300)
        self.confirm_pw.pack(pady=10)

        self.setup_error = ctk.CTkLabel(setup_frame, text="", text_color="red")
        self.setup_error.pack()

        def set_master_password(): # Changed
            password = self.new_pw.get()
            password_confirm = self.confirm_pw.get()
            if len(password) < 8:
                self.setup_error.configure(text="Your password must be at least 8 characters!")
                return
            if password != password_confirm:
                self.setup_error.configure(text="Passwords do not match!")
                return
            
            store_key(password)
            messagebox.showinfo("Success", "Master password set! Please login.")
            self.show_lock_window()

        ctk.CTkButton(setup_frame, text="Save", corner_radius=20, command=set_master_password).pack(pady=30) # Changed

    # --- SCREEN 1: LOCK WINDOW (Login) ---
    def show_lock_window(self):
        self.clear_screen()
        lock_frame = ctk.CTkFrame(self.main_container, fg_color="#D0EFFF", corner_radius=30, width=500, height=450)
        lock_frame.place(relx=0.5, rely=0.5, anchor="center")
        lock_frame.pack_propagate(False)

        logo_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        logo_raw = Image.open(logo_path)
        logo_img = ctk.CTkImage(light_image=logo_raw, dark_image=logo_raw, size=(100, 100))

        logo_label = ctk.CTkLabel(lock_frame, image=logo_img, text="")
        logo_label.pack(pady=(40, 5))

        ctk.CTkLabel(lock_frame, text="Password Manager", font=("Helvetica", 34), text_color="black").pack(pady=5)

        self.pw_entry = ctk.CTkEntry(lock_frame, placeholder_text="Enter Key", show="*", width=250, height=35, corner_radius=20, border_width=0)
        self.pw_entry.pack(pady=20)

        enter_btn = ctk.CTkButton(lock_frame, text="Enter", corner_radius=15, width=120, height=35, 
                                 command=self.handle_login, fg_color="#3B8ED0", hover_color="#3A4E7C")
        enter_btn.pack(pady=5)

        setup_link = ctk.CTkLabel(lock_frame, text="First Time?\nSet Up Master Password", 
                              font=("Helvetica", 11, "underline"), cursor="hand2", text_color="black")
        setup_link.pack(pady=10)
        setup_link.bind("<Button-1>", lambda e: self.show_first_time_setup())

    def handle_login(self):
        password = self.pw_entry.get()
        if not password:
            messagebox.showwarning("Input Error", "Please enter your master password.")
            return

        try:
            self.current_user_key = verify_key(password) # Changed
            if self.current_user_key:
                self.db_conn = database.initialize_database(self.current_user_key)
                self.show_main_window()
            else:
                messagebox.showerror("Access Denied", "Incorrect Master Password")
        except Exception as e:
            # This is where the auth_store.json error used to happen
            messagebox.showerror("Error", f"Login failed: {e}")

    # --- SCREEN 2: MAIN WINDOW (The Vault) ---
    def show_main_window(self):
        self.clear_screen()

        self.sidebar = ctk.CTkFrame(self.main_container, fg_color="#89CFF0", width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="SecVault", font=("Helvetica", 20, "bold")).pack(pady=20)

        for category in ["All", "Work", "Personal", "Wifi"]:
            btn = ctk.CTkButton(self.sidebar, text=category, fg_color="#3B8ED0", corner_radius=10,
                               command=lambda c=category: self.load_vault_data(c))
            btn.pack(pady=10, padx=20, fill="x")

        # Changes made to this section
        add_btn = ctk.CTkButton(self.sidebar, text="+ Add Entry", 
                                # font=("Arial", 20), width=40, # Test
                               command=self.show_add_password_window)
        add_btn.pack(pady=50) 

        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="white", corner_radius=15)
        self.scroll_frame.pack(fill="both", expand=True, pady=10)

        self.load_vault_data("All")

    def load_vault_data(self, category_filter):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        cursor = self.db_conn.cursor()
        if category_filter == "All":
            cursor.execute("SELECT id, service, username, password FROM vault")
        else:
            cursor.execute("SELECT id, service, username, password FROM vault WHERE category = ?", (category_filter,))
        
        for row in cursor.fetchall():
            self.create_password_row(row)

    def create_password_row(self, data):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#F0F8FF", height=50)
        row_frame.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(row_frame, text=data[1], font=("Arial", 14, "bold"), width=150).pack(side="left", padx=10)
        ctk.CTkLabel(row_frame, text="••••••••", width=150).pack(side="left", padx=10)
        
        # Action Buttons
        ctk.CTkButton(row_frame, text="⚙️", width=30, 
                     command=lambda d=data: self.show_options_menu(d)).pack(side="right", padx=5)
        
        ctk.CTkButton(row_frame, text="👁️", width=30, 
                     command=lambda: messagebox.showinfo("Credentials", f"Service: {data[1]}\nUser: {data[2]}\nPass: {data[3]}")).pack(side="right", padx=5)

    # --- NEW: UPDATE/DELETE POPUP (The "Changes View") ---
    def show_options_menu(self, data):
        opt_win = ctk.CTkToplevel(self)
        opt_win.title("Options")
        opt_win.geometry("250x150")
        opt_win.attributes("-topmost", True)

        def update_password_entry():
            new_password = simpledialog.askstring("Update", f"New password for {data[1]}:")
            if new_password:
                cursor = self.db_conn.cursor()
                cursor.execute("UPDATE vault SET password = ? WHERE id = ?", (new_password, data[0]))
                self.db_conn.commit()
                opt_win.destroy()
                self.load_vault_data("All")

        def delete_password_entry():
            if messagebox.askyesno("Confirm", "Delete this entry?"):
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM vault WHERE id = ?", (data[0],))
                self.db_conn.commit()
                opt_win.destroy()
                self.load_vault_data("All")

        ctk.CTkButton(opt_win, text="Change/Update", command=update_password_entry).pack(pady=10)
        ctk.CTkButton(opt_win, text="Delete", fg_color="red", command=delete_password_entry).pack(pady=10)

    # --- SCREEN 3: ADD WINDOW ---
    def show_add_password_window(self):
        add_win = ctk.CTkToplevel(self)
        add_win.title("Add Credential")
        add_win.geometry("400x500")
        add_win.attributes("-topmost", True)

        ctk.CTkLabel(add_win, text="Add New Credential", font=("Arial", 18, "bold")).pack(pady=20)
        service_in = ctk.CTkEntry(add_win, placeholder_text="Service", width=250)
        service_in.pack(pady=10)
        user_in = ctk.CTkEntry(add_win, placeholder_text="Username", width=250)
        user_in.pack(pady=10)
        pass_in = ctk.CTkEntry(add_win, placeholder_text="Password", width=250)
        pass_in.pack(pady=10)

        def gen():
            new_p = passforge.password_generator()
            pass_in.delete(0, 'end')
            pass_in.insert(0, new_p)

        ctk.CTkButton(add_win, text="Generate Strong Password", command=gen, fg_color="gray").pack(pady=5)
        cat_var = ctk.StringVar(value="Work")
        ctk.CTkOptionMenu(add_win, values=["Work", "Personal", "Wifi"], variable=cat_var).pack(pady=10)

        def save_password_entry():
            cursor = self.db_conn.cursor()
            cursor.execute('INSERT INTO vault (service, username, password, category) VALUES (?, ?, ?, ?)',
                          (service_in.get(), user_in.get(), pass_in.get(), cat_var.get()))
            self.db_conn.commit()
            add_win.destroy()
            self.load_vault_data("All")

        ctk.CTkButton(add_win, text="Save", command=save_password_entry, fg_color="#28a745").pack(pady=20)

if __name__ == "__main__":
    app = SecVaultApp()
    app.mainloop()