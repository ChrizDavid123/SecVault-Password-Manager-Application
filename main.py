import os
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image
import database
import authentication
import passforge
from secrets import token_bytes

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
        outside_logo = self.new_method(logo_img)
        outside_logo.place(relx=0.5, rely=0.19, anchor="center")

        setup_frame = ctk.CTkFrame(self.main_container, fg_color="#CDEBFF", corner_radius=20, width=500, height=350)
        setup_frame.pack_propagate(False)
        setup_frame.place(relx=0.5, rely=0.55, anchor="center")

        p2_container = self.new_method1(setup_frame)

        def toggle_p2():
            if self.confirm_pw.cget("show") == "*":
                self.confirm_pw.configure(show="")
                eye_p2.configure(text="🔒")
            else:
                self.confirm_pw.configure(show="*")
                eye_p2.configure(text="👁️")

        eye_p2 = ctk.CTkButton(p2_container, text="👁️", width=30, height=30, fg_color="transparent", 
                               text_color="#318ba2", font=("Arial", 18), command=toggle_p2)
        eye_p2.pack(side="right", padx=5)

        # Error label and Save button
        self.setup_error = ctk.CTkLabel(setup_frame, text="", text_color="red")
        self.setup_error.pack()

        def save_master():
            p1 = self.new_pw.get()
            p2 = self.confirm_pw.get()
            if len(p1) < 8:
                self.setup_error.configure(text="Your password must be at least 8 characters!")
                return
            if p1 != p2:
                self.setup_error.configure(text="Passwords do not match!")
                return

            authentication.store_key(p1)
            messagebox.showinfo("Success", "Master password set!")
            self.show_lock_window()

        ctk.CTkButton(setup_frame, text="Save", corner_radius=20, width=150, height=40,
                     fg_color="#3B8ED0", command=save_master).pack(pady=20)

    def new_method1(self, setup_frame):
        ctk.CTkLabel(setup_frame, text="Set Up Master Password", font=("Helvetica", 24, "bold"), text_color="black").pack(pady=20)

        # --- 1. MAKE PASSWORD BAR ---
        p1_container = ctk.CTkFrame(setup_frame, fg_color="white", corner_radius=10, width=350, height=40)
        p1_container.pack(pady=10)
        p1_container.pack_propagate(False)

        self.new_pw = ctk.CTkEntry(p1_container, placeholder_text="Make Password", show="*", 
                                   border_width=0, fg_color="white", text_color="black")
        self.new_pw.pack(side="left", padx=(10, 0), fill="x", expand=True)

        def toggle_p1():
            if self.new_pw.cget("show") == "*":
                self.new_pw.configure(show="")
                eye_p1.configure(text="🔒")
            else:
                self.new_pw.configure(show="*")
                eye_p1.configure(text="👁️")

        eye_p1 = ctk.CTkButton(p1_container, text="👁️", width=30, height=30, fg_color="transparent", 
                               text_color="#318ba2", font=("Arial", 18), command=toggle_p1)
        eye_p1.pack(side="right", padx=5)

        p2_container = ctk.CTkFrame(setup_frame, fg_color="white", corner_radius=10, width=350, height=40)
        p2_container.pack(pady=10)
        p2_container.pack_propagate(False)

        self.confirm_pw = ctk.CTkEntry(p2_container, placeholder_text="Confirm Password", show="*", 
                                       border_width=0, fg_color="white", text_color="black")
        self.confirm_pw.pack(side="left", padx=(10, 0), fill="x", expand=True)
        return p2_container

    def new_method(self, logo_img):
        outside_logo = ctk.CTkLabel(self.main_container, image=logo_img, text="")
        return outside_logo

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

        entry_container = ctk.CTkFrame(lock_frame, fg_color="white", corner_radius=20, width=300, height=40)
        entry_container.pack(pady=20)
        entry_container.pack_propagate(False)

        self.pw_entry = ctk.CTkEntry(entry_container, placeholder_text="Enter Key", show="*", height=45, border_width=0, fg_color="white", text_color="black")
        self.pw_entry.pack(side="left", padx=(15, 0), fill="x", expand=True)

        def toggle_password():
            if self.pw_entry.cget("show") == "*":
                self.pw_entry.configure(show="")
                eye_btn.configure(text="🔒", text_color="#318ba2") 
            else:
                self.pw_entry.configure(show="*")
                eye_btn.configure(text="👁️", text_color="#318ba2") 

        eye_btn = ctk.CTkButton(
            entry_container, 
            text="👁️", 
            width=10,            
            height=35, 
            corner_radius=20, 
            fg_color="transparent", 
            text_color="#318ba2",
            hover_color="#EEEEEE",
            font=("Arial", 15),   
            command=toggle_password
        )
        eye_btn.pack(side="right", padx=10)
        
        enter_btn = ctk.CTkButton(lock_frame, text="Enter", corner_radius=15, width=120, height=35, 
                                 command=self.handle_login, fg_color="#3B8ED0", hover_color="#3A4E7C")
        enter_btn.pack(pady=5)

        setup_link = ctk.CTkLabel(lock_frame, text="First Time?\nSet Up Master Password", 
                              font=("Helvetica", 11, "underline"), cursor="hand2", text_color="black")
        setup_link.pack(pady=10)
        setup_link.bind("<Button-1>", lambda e: self.show_first_time_setup())
        

    def handle_login(self):
        pwd = self.pw_entry.get()
        if not pwd:
            messagebox.showwarning("Input Error", "Please enter your master password.")
            return

        try:
            self.current_user_key = authentication.verify_key(pwd)
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

        # 1. Sidebar Setup
        self.sidebar = ctk.CTkFrame(self.main_container, fg_color="#7ba8cc", width=220, corner_radius=20)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        self.sidebar.pack_propagate(False)

        # Categories
        for cat in ["All", "Work", "Personal", "Wifi"]:
            # Highlight 'All' by default to match design
            bg = "#4a6291" if cat == "All" else "black"
            btn = ctk.CTkButton(self.sidebar, text=cat, fg_color=bg, text_color="white",
                                corner_radius=15, height=35, font=("Helvetica", 14, "bold"),
                                command=lambda c=cat: self.load_vault_data(c))
            btn.pack(pady=10, padx=25, fill="x")

        # Add Button (Circular)
        add_btn = ctk.CTkButton(self.sidebar, text="+", font=("Arial", 24), width=50, height=50,
                               fg_color="transparent", border_width=2, border_color="black",
                               text_color="black", corner_radius=25,
                               command=self.show_add_password_window)
        add_btn.pack(pady=20)

        # LOCK VAULT BUTTON (Bottom of Sidebar)
        lock_btn = ctk.CTkButton(self.sidebar, text="↪ Lock Vault", fg_color="transparent", 
                                text_color="white", font=("Helvetica", 16, "bold"),
                                hover_color="#6b97ba", command=self.show_lock_window)
        lock_btn.pack(side="bottom", pady=30)

        # 2. Main Content Area
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#D0EFFF")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Top Bar (Search & Settings)
        top_bar = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(20, 10))

        search_entry = ctk.CTkEntry(top_bar, placeholder_text="Search", height=35, 
                                   corner_radius=20, fg_color="#d9d9d9", border_width=0)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        settings_btn = ctk.CTkButton(top_bar, text="⚙️", width=35, height=35, 
                                    fg_color="transparent", text_color="black", font=("Arial", 20))
        settings_btn.pack(side="right")

        # Scrollable Area for Password Rows
        self.scroll_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=10)

        self.load_vault_data("All")

    def create_password_row(self, data):
        # Frame for the whole row
        row_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_container.pack(fill="x", pady=8, padx=10)

        # Icon Placeholder (e.g., Circle for Service Logo)
        icon_lbl = ctk.CTkLabel(row_container, text="🔵", font=("Arial", 18))
        icon_lbl.pack(side="left", padx=5)

        # The White "Password Bar"
        bar = ctk.CTkFrame(row_container, fg_color="white", height=35, corner_radius=5, border_width=1)
        bar.pack(side="left", fill="x", expand=True, padx=5)
        bar.pack_propagate(False)

        # Service Name & Masked Password
        label_text = f"{data[1]}:  ****************"
        ctk.CTkLabel(bar, text=label_text, text_color="black", font=("Helvetica", 12)).pack(side="left", padx=10)

        # Mini Buttons inside the bar (Copy & View)
        copy_btn = ctk.CTkButton(bar, text="📋", width=25, height=25, fg_color="transparent", 
                                text_color="gray", font=("Arial", 12))
        copy_btn.pack(side="right", padx=2)
        
        view_btn = ctk.CTkButton(bar, text="👁️", width=25, height=25, fg_color="transparent", 
                                text_color="#318ba2", font=("Arial", 12))
        view_btn.pack(side="right", padx=2)

        # Options Menu (The Three Dots)
        dots_btn = ctk.CTkButton(row_container, text="⋮", width=20, fg_color="transparent", 
                                text_color="black", font=("Arial", 20),
                                command=lambda: self.show_options_menu(data))
        dots_btn.pack(side="right")

    # --- NEW: UPDATE/DELETE POPUP (The "Changes View") ---
    def show_options_menu(self, data):
        opt_win = ctk.CTkToplevel(self)
        opt_win.title("Options")
        opt_win.geometry("250x150")
        opt_win.attributes("-topmost", True)

        def update_p():
            new_p = simpledialog.askstring("Update", f"New password for {data[1]}:")
            if new_p:
                cursor = self.db_conn.cursor()
                cursor.execute("UPDATE vault SET password = ? WHERE id = ?", (new_p, data[0]))
                self.db_conn.commit()
                opt_win.destroy()
                self.load_vault_data("All")

        def delete_p():
            if messagebox.askyesno("Confirm", "Delete this entry?"):
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM vault WHERE id = ?", (data[0],))
                self.db_conn.commit()
                opt_win.destroy()
                self.load_vault_data("All")

        ctk.CTkButton(opt_win, text="Change/Update", command=update_p).pack(pady=10)
        ctk.CTkButton(opt_win, text="Delete", fg_color="red", command=delete_p).pack(pady=10)

    # --- SCREEN 3: ADD WINDOW ---
    def show_add_password_window(self):
        add_win = ctk.CTkToplevel(self)
        add_win.title("Add Credential")
        add_win.geometry("400x500")
        add_win.attributes("-topmost", True)

        icon_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        def apply_popup_icon():
            img = tk.PhotoImage(file=icon_path)
            add_win.iconphoto(False, img)
        add_win.after(200, apply_popup_icon)

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

        def save():
            cursor = self.db_conn.cursor()
            cursor.execute('INSERT INTO vault (service, username, password, category) VALUES (?, ?, ?, ?)',
                          (service_in.get(), user_in.get(), pass_in.get(), cat_var.get()))
            cursor.execute("SELECT CategoryID FROM Category WHERE Name = ?", (cat_var.get(),))
            cat_id = cursor.fetchone()[0]

            cursor.execute('''
                INSERT INTO VaultEntry (Service, Username, Password, CategoryID) 
                VALUES (?, ?, ?, ?)
            ''', (service_in.get(), user_in.get(), pass_in.get(), cat_id))
            self.db_conn.commit()
            add_win.destroy()
            self.load_vault_data("All")



        ctk.CTkButton(add_win, text="Save", command=save, fg_color="#28a745").pack(pady=20)

if __name__ == "__main__":
    app = SecVaultApp()
    app.mainloop()