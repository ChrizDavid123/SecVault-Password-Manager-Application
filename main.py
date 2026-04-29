import os
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image
import database
import authentication
import passforge

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Colour palette (single source of truth) ──────────────────────────────────
BG_OUTER   = "#C8DFF0"   # window background
BG_CARD    = "#AACFE8"   # cards / sidebar
BG_PANEL   = "#BDD9EE"   # main content area
BG_POPUP   = "#7ba8cc"   # popup / options frame
BTN_ACTIVE = "#2f5f8f"   # selected category
BTN_IDLE   = "#1a1a2e"   # unselected category
BTN_HOVER  = "#3a6fa8"   # hover
WHITE      = "#ffffff"
TEXT_DARK  = "#0d1b2a"
TEXT_LIGHT = "#ffffff"
BLUE_BTN   = "#2d7dd2"
GREEN_BTN  = "#28a745"
RED_BTN    = "#d9534f"


class SecVaultApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SecVault")
        self.geometry("1100x700")
        self.resizable(0, 0)
        self.configure(fg_color=BG_OUTER)

        # Set database connection to None
        self.db_conn = None

        icon_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        self.after(200, lambda: self._apply_icon(icon_path))


    # ── Helpers ───────────────────────────────────────────────────────────────
    def _apply_icon(self, path):
        try:
            img = tk.PhotoImage(file=path)
            self.iconphoto(False, img)
        except Exception as e:
            print(f"Icon Error: {e}")

        self.main_container = ctk.CTkFrame(self, fg_color=BG_OUTER)
        self.main_container.pack(fill="both", expand=True)
        self.check_initial_state()

    def _popup_icon(self, win):
        icon_path = os.path.join(os.path.dirname(__file__), "AppLogo.png")
        def _set():
            try:
                img = tk.PhotoImage(file=icon_path)
                win.iconphoto(False, img)
            except Exception:
                pass
        win.after(200, _set)

    def check_initial_state(self):
        auth_file = Path("auth_store.json")
        if not auth_file.exists() or auth_file.stat().st_size == 0:
            self.show_first_time_setup()
        else:
            self.show_lock_window()

    def clear_screen(self):
        for w in self.main_container.winfo_children():
            w.destroy()


    # ── SETUP SCREEN ──────────────────────────────────────────────────────────
    def show_first_time_setup(self):
        self.clear_screen()

        # Logo above the card
        logo_raw = Image.open(os.path.join(os.path.dirname(__file__), "AppLogo.png"))
        logo_img = ctk.CTkImage(light_image=logo_raw, dark_image=logo_raw, size=(90, 90))
        ctk.CTkLabel(self.main_container, image=logo_img, text="").place(relx=0.5, rely=0.16, anchor="center")

        # Card
        card = ctk.CTkFrame(self.main_container, fg_color=BG_CARD, corner_radius=18,
                            width=480, height=340)
        card.pack_propagate(False)
        card.place(relx=0.5, rely=0.55, anchor="center")

        ctk.CTkLabel(card, text="Set Up Master Password",
                     font=("Helvetica", 22, "bold"), text_color=TEXT_DARK).pack(pady=(24, 16))

        def _field_row(parent, placeholder):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(pady=6)
            container = ctk.CTkFrame(row, fg_color=WHITE, corner_radius=10, width=340, height=38)
            container.pack_propagate(False)
            container.pack()
            entry = ctk.CTkEntry(container, placeholder_text=placeholder, show="*",
                                 border_width=0, fg_color=WHITE, text_color=TEXT_DARK)
            entry.pack(side="left", padx=(12, 0), fill="x", expand=True)
            return container, entry

        c1, self.new_pw     = _field_row(card, "Make Password")
        c2, self.confirm_pw = _field_row(card, "Confirm Password")

        # Password visibility toggle buttons
        for container, entry in [(c1, self.new_pw), (c2, self.confirm_pw)]:
            def _toggle(en=entry, btn_ref=[None]):
                if en.cget("show") == "*":
                    en.configure(show="")
                    if btn_ref[0]: btn_ref[0].configure(text="Hide")
                else:
                    en.configure(show="*")
                    if btn_ref[0]: btn_ref[0].configure(text="Show")

            # Toggle button
            toggle_button = ctk.CTkButton(container, text="Show", width=30, height=30,
                              fg_color="transparent", text_color="#318ba2",
                              font=("Arial", 12), command=_toggle)
            toggle_button.pack(side="right", padx=4)

            # Wire the button reference so toggle can update it
            def _toggle_password_visibility(en, btn):
                def _t():
                    if en.cget("show") == "*":
                        en.configure(show="")
                        btn.configure(text="Hide")
                    else:
                        en.configure(show="*")
                        btn.configure(text="Show")
                return _t
            
            toggle_button.configure(command=_toggle_password_visibility(entry, toggle_button))

        self.setup_error = ctk.CTkLabel(card, text="", text_color=RED_BTN,
                                        font=("Helvetica", 11))
        self.setup_error.pack(pady=(6, 0))

        def save_master_password():
            __password, __password_confirm = self.new_pw.get(), self.confirm_pw.get()
            if len(__password) < 8:
                self.setup_error.configure(text="Password must be at least 8 characters!")
                return
            if __password != __password_confirm:
                self.setup_error.configure(text="Passwords do not match!")
                return
            
            __key = authentication.store_key(__password) # Store key (hash) and salt into auth_store.json file
            self.db_conn = database.initialize_database(__key) # Create database
            messagebox.showinfo("Success", "Master password set!")

            # Redirect to main window after create master password
            self.main_window()

        ctk.CTkButton(card, text="Save", corner_radius=20, width=140, height=38,
                      fg_color=BLUE_BTN, hover_color=BTN_HOVER,
                      font=("Helvetica", 14, "bold"), command=save_master_password).pack(pady=16)


    # ── LOCK WINDOW ───────────────────────────────────────────────────────────
    def show_lock_window(self):
        self.clear_screen()

        card = ctk.CTkFrame(self.main_container, fg_color=BG_CARD,
                            corner_radius=28, width=460, height=440)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        logo_raw = Image.open(os.path.join(os.path.dirname(__file__), "AppLogo.png"))
        logo_img = ctk.CTkImage(light_image=logo_raw, dark_image=logo_raw, size=(95, 95))
        ctk.CTkLabel(card, image=logo_img, text="").pack(pady=(36, 6))

        ctk.CTkLabel(card, text="Password Manager",
                     font=("Helvetica", 30, "bold"), text_color=TEXT_DARK).pack(pady=(0, 20))

        # Entry row
        entry_row = ctk.CTkFrame(card, fg_color=WHITE, corner_radius=20, width=300, height=40)
        entry_row.pack_propagate(False)
        entry_row.pack(pady=4)

        self.password_entry = ctk.CTkEntry(entry_row, placeholder_text="Enter Key", show="*",
                                     height=40, border_width=0, fg_color=WHITE, text_color=TEXT_DARK)
        self.password_entry.pack(side="left", padx=(14, 0), fill="x", expand=True)

        def _toggle_password_visibility():
            if self.password_entry.cget("show") == "*":
                self.password_entry.configure(show="")
                toggle_button.configure(text="Hide")
            else:
                self.password_entry.configure(show="*")
                toggle_button.configure(text="Show")

        toggle_button = ctk.CTkButton(entry_row, text="Show", width=34, height=34,
                                corner_radius=17, fg_color="transparent",
                                text_color="#318ba2", hover_color="#EEEEEE",
                                font=("Arial", 12), command=_toggle_password_visibility)
        toggle_button.pack(side="right", padx=6)

        ctk.CTkButton(card, text="Enter", corner_radius=14, width=120, height=36,
                      fg_color=BLUE_BTN, hover_color=BTN_HOVER,
                      font=("Helvetica", 13, "bold"),
                      command=self.handle_login).pack(pady=16)

    def handle_login(self):
        __password = self.password_entry.get()
        if not __password or not __password.strip():
            messagebox.showwarning("Input Error", "Please enter your master password.")
            return
        try:
            __key = authentication.verify_key(__password)
            __conn = database.access_database(__key)
        except Exception:
            messagebox.showerror("Error", "Master password is invalid!")
            return
        finally:
            self.db_conn = __conn
            self.main_window()


    # ── MAIN WINDOW ───────────────────────────────────────────────────────────
    def main_window(self):
        self.clear_screen()

        # ── Sidebar ──────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(self.main_container, fg_color=BG_POPUP,
                               width=200, corner_radius=18)
        sidebar.pack(side="left", fill="y", padx=(10, 6), pady=10)
        sidebar.pack_propagate(False)

        # Category buttons
        self.category_buttons = {}

        def select_category(cat):
            for c, b in self.category_buttons.items():
                b.configure(fg_color=BTN_ACTIVE if c == cat else BTN_IDLE)
            self.load_vault_data(cat)

        ctk.CTkLabel(sidebar, text="", height=20).pack()

        for cat in ["All", "Work", "Personal", "WiFi"]:
            bg = BTN_ACTIVE if cat == "All" else BTN_IDLE
            btn = ctk.CTkButton(sidebar, text=cat, fg_color=bg,
                                text_color=TEXT_LIGHT, corner_radius=14,
                                height=34, font=("Helvetica", 13, "bold"),
                                hover_color=BTN_HOVER,
                                command=lambda c=cat: select_category(c))
            btn.pack(pady=5, padx=18, fill="x")
            self.category_buttons[cat] = btn

        # Add (+) button
        ctk.CTkButton(sidebar, text="+", font=("Arial", 22, "bold"),
                      width=46, height=46, corner_radius=23,
                      fg_color="transparent", border_width=2,
                      border_color=TEXT_LIGHT, text_color=TEXT_LIGHT,
                      hover_color=BTN_HOVER,
                      command=self.show_add_password_window).pack(pady=18)

        # Closes database connection and locks vault
        def lock_vault():
            database.log_auth_event(self.db_conn, "LOGOUT")
            self.db_conn.close()
            self.show_lock_window()

        # Lock Vault (bottom)
        ctk.CTkButton(sidebar, text="↪  Lock Vault",
                      fg_color="transparent", text_color=TEXT_LIGHT,
                      font=("Helvetica", 13, "bold"),
                      hover_color=BTN_HOVER,
                      command=lock_vault).pack(side="bottom", pady=22)
        

        # ── Content area ─────────────────────────────────────────────────────
        content = ctk.CTkFrame(self.main_container, fg_color=BG_PANEL, corner_radius=18)
        content.pack(side="right", fill="both", expand=True,
                     padx=(4, 10), pady=10)

        # Top bar
        top_bar = ctk.CTkFrame(content, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(14, 6))

        search_frame = ctk.CTkFrame(top_bar, fg_color=WHITE, corner_radius=17,
                            height=34)
        search_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))
        search_frame.pack_propagate(False)

        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search",
                                    height=34, corner_radius=17,
                                    fg_color=WHITE, border_width=0,
                                    text_color=TEXT_DARK)
        search_entry.pack(side="left", fill="x", expand=True, padx=(12, 0))

        ctk.CTkLabel(search_frame, text="🔍", font=("Arial", 14),
                    text_color="#888").pack(side="right", padx=10)

        ctk.CTkButton(top_bar, text="⚙️", width=34, height=34,
                      fg_color="transparent", text_color=TEXT_DARK,
                      font=("Arial", 18), hover_color="#cce0f0",
                      command=self.show_settings_window).pack(side="right")

        # Scrollable list
        self.scroll_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.load_vault_data("All")


    # ── PASSWORD ROW ──────────────────────────────────────────────────────────
    # Cycle of accent colours for the service icon dot
    _ICON_COLORS = ["#4285F4", "#34A853", "#EA4335", "#FBBC05",
                    "#9C27B0", "#FF5722", "#00BCD4", "#607D8B"]

    def create_password_row(self, data, idx=0):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=5, padx=6)

        # Coloured circle icon
        color = self._ICON_COLORS[idx % len(self._ICON_COLORS)]
        icon_lbl = ctk.CTkLabel(row, text="●", font=("Arial", 22),
                                text_color=color, width=28)
        icon_lbl.pack(side="left", padx=(2, 4))

        # White bar
        bar = ctk.CTkFrame(row, fg_color=WHITE, height=36,
                           corner_radius=8, border_width=0)
        bar.pack(side="left", fill="x", expand=True, padx=4)
        bar.pack_propagate(False)

        masked = f"{data[1]}   ················"
        pw_label = ctk.CTkLabel(bar, text=masked,
                                text_color=TEXT_DARK,
                                font=("Helvetica", 12), anchor="w")
        pw_label.pack(side="left", padx=12, fill="x", expand=True)

        # View toggle
        def _toggle_password_visibility():
            if "·" in pw_label.cget("text"):
                pw_label.configure(text=f"{data[1]}   {data[3]}")
                toggle_button.configure(text="Hide")
            else:
                pw_label.configure(text=masked)
                toggle_button.configure(text="Show")

        toggle_button = ctk.CTkButton(bar, text="Show", width=26, height=26,
                                 fg_color="transparent", text_color="#318ba2",
                                 font=("Arial", 12), hover_color="#eaf4ff",
                                 command=_toggle_password_visibility)
        toggle_button.pack(side="right", padx=2)

        # Copy to clipboard
        def copy_pw():
            self.clipboard_clear()
            self.clipboard_append(data[3])
            self.update()
            copy_btn.configure(text="✅")
            copy_btn.after(1400, lambda: copy_btn.configure(text="📋"))

        copy_btn = ctk.CTkButton(bar, text="📋", width=26, height=26,
                                 fg_color="transparent", text_color="#666",
                                 font=("Arial", 13), hover_color="#eaf4ff",
                                 command=copy_pw)
        copy_btn.pack(side="right", padx=2)

        # Three-dots
        ctk.CTkButton(row, text="⋮", width=22, fg_color="transparent",
                      text_color=TEXT_DARK, font=("Arial", 20),
                      hover_color="#cce0f0",
                      command=lambda: self.show_options_menu(data)).pack(side="right")


    # ── OPTIONS MENU (Changes View) ───────────────────────────────────────────
    def show_options_menu(self, data):
        win = ctk.CTkToplevel(self)
        win.title("")
        win.geometry("220x160")
        win.resizable(0, 0)
        win.attributes("-topmost", True)
        self._popup_icon(win)

        frame = ctk.CTkFrame(win, fg_color=BG_POPUP, corner_radius=14)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        def update_password_entry():
            new_p = simpledialog.askstring("Update", f"New password for {data[1]}:", parent=win)
            if new_p:
                cur = self.db_conn.cursor()
                cur.execute("UPDATE Vault_Entry SET Password = ? WHERE EntryID = ?",
                            (new_p, data[0]))
                self.db_conn.commit()
                win.destroy()
                self.load_vault_data("All")

        def delete_password_entry():
            if messagebox.askyesno("Confirm", "Delete this entry?", parent=win):
                cur = self.db_conn.cursor()
                cur.execute("DELETE FROM Vault_Entry WHERE EntryID = ?", (data[0],))
                self.db_conn.commit()
                win.destroy()
                self.load_vault_data("All")

        ctk.CTkButton(frame, text="Change / Update",
                      fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
                      hover_color=BTN_HOVER, corner_radius=16,
                      height=36, font=("Helvetica", 13, "bold"),
                      command=update_password_entry).pack(pady=(18, 8), padx=18, fill="x")

        ctk.CTkButton(frame, text="Delete",
                      fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
                      hover_color=RED_BTN, corner_radius=16,
                      height=36, font=("Helvetica", 13, "bold"),
                      command=delete_password_entry).pack(pady=(0, 8), padx=18, fill="x")


    # ── SETTINGS WINDOW ───────────────────────────────────────────────────────
    def show_settings_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Settings")
        win.geometry("620x400")
        win.resizable(0, 0)
        win.attributes("-topmost", True)
        self._popup_icon(win)

        main_frame = ctk.CTkFrame(win, fg_color=BG_CARD, corner_radius=16)
        main_frame.pack(fill="both", expand=True, padx=14, pady=14)

        def change_master_password_window():
            # Clear contents of previous screen
            for w in main_frame.winfo_children():
                w.destroy()

            def _field_row(parent, placeholder):
                row = ctk.CTkFrame(parent, fg_color="transparent")
                row.pack(pady=6)
                container = ctk.CTkFrame(row, fg_color=WHITE, corner_radius=10, width=340, height=38)
                container.pack_propagate(False)
                container.pack()
                entry = ctk.CTkEntry(container, placeholder_text=placeholder, show="*",
                                    border_width=0, fg_color=WHITE, text_color=TEXT_DARK)
                entry.pack(side="left", padx=(12, 0), fill="x", expand=True)
                return container, entry

            c1, self.new_pw     = _field_row(main_frame, "Make Password")
            c2, self.confirm_pw = _field_row(main_frame, "Confirm Password")

            # Show-hide buttons
            for container, entry in [(c1, self.new_pw), (c2, self.confirm_pw)]:
                def _toggle(en=entry, btn_ref=[None]):
                    if en.cget("show") == "*":
                        en.configure(show="")
                        if btn_ref[0]: btn_ref[0].configure(text="Hide")
                    else:
                        en.configure(show="*")
                        if btn_ref[0]: btn_ref[0].configure(text="Show")
                b = ctk.CTkButton(container, text="Show", width=30, height=30,
                                fg_color="transparent", text_color="#318ba2",
                                font=("Arial", 12), command=_toggle)
                b.pack(side="right", padx=4)
                # Wire the button reference so toggle can update it
                def _toggle_password_visibility(en, btn):
                    def _t():
                        if en.cget("show") == "*":
                            en.configure(show="")
                            btn.configure(text="Hide")
                        else:
                            en.configure(show="*")
                            btn.configure(text="Show")
                    return _t
                b.configure(command=_toggle_password_visibility(entry, b))

            self.setup_error = ctk.CTkLabel(main_frame, text="", text_color=RED_BTN,
                                            font=("Helvetica", 11))
            self.setup_error.pack(pady=(6, 0))

            def change_master_password():
                p1, p2 = self.new_pw.get(), self.confirm_pw.get()
                if len(p1) < 8:
                    self.setup_error.configure(text="Password must be at least 8 characters!")
                    return
                if p1 != p2:
                    self.setup_error.configure(text="Passwords do not match!")
                    return
                key = authentication.store_key(p1)
                self.db_conn = database.change_key(self.db_conn, key)
                messagebox.showinfo("Success", "Master password set!")

                # Redirect to main window after create master password
                win.destroy()

                self.show_lock_window()

            ctk.CTkButton(main_frame, text="Save", corner_radius=20, width=140, height=38,
                        fg_color=BLUE_BTN, hover_color=BTN_HOVER,
                        font=("Helvetica", 14, "bold"), command=change_master_password).pack(pady=16)

        def delete_account():
            if messagebox.askyesno("Confirm Delete",
                                    "Delete ALL data permanently?", parent=win):
                
                # Delete authentication data
                Path("auth_store.json").unlink()

                # Delete database
                database.delete_vault(self.db_conn)

                # opt.destroy()
                win.destroy()

                # Show first time setup window
                self.show_first_time_setup()

        # Change master password
        ctk.CTkButton(main_frame, text="Change Master Password",
                fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
                hover_color=RED_BTN, corner_radius=18,
                width=160, height=40,
                font=("Helvetica", 13, "bold"),
                command=change_master_password_window).pack(pady=(70, 6))
        
        # Delete Account button
        ctk.CTkButton(main_frame, text="Delete Account",
                      fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
                      hover_color=RED_BTN, corner_radius=18,
                      width=160, height=40,
                      font=("Helvetica", 13, "bold"),
                      command=delete_account).pack(pady=(70, 6))

        ctk.CTkLabel(main_frame,
                     text="Note: Are you sure you want to delete the account?\n"
                          "You won't be able to recover your data",
                     font=("Helvetica", 10), text_color="#555").pack()


    # ── ADD PASSWORD WINDOW ───────────────────────────────────────────────────
    def show_add_password_window(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Credential")
        win.geometry("400x460")
        win.resizable(0, 0)
        win.attributes("-topmost", True)
        self._popup_icon(win)
        win.configure(fg_color=BG_OUTER)

        inner = ctk.CTkFrame(win, fg_color=BG_CARD, corner_radius=16)
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(inner, text="Add New Credential",
                     font=("Helvetica", 18, "bold"),
                     text_color=TEXT_DARK).pack(pady=(20, 14))

        def _entry(placeholder):
            entry = ctk.CTkEntry(inner, placeholder_text=placeholder, width=280,
                             height=36, corner_radius=10,
                             fg_color=WHITE, border_width=0,
                             text_color=TEXT_DARK)
            entry.pack(pady=6)
            return entry

        service_in = _entry("Service")
        user_in    = _entry("Username")
        pass_in    = _entry("Password")

        def generate_password():
            new_p = passforge.password_generator()
            pass_in.delete(0, "end")
            pass_in.insert(0, new_p)

        ctk.CTkButton(inner, text="⚡  Generate Strong Password",
                      command=generate_password, fg_color="#4a4a6a",
                      hover_color="#5a5a8a", corner_radius=14,
                      width=280, height=34,
                      font=("Helvetica", 12)).pack(pady=6)

        cat_var = ctk.StringVar(value="Work")
        ctk.CTkOptionMenu(inner, values=["Work", "Personal", "WiFi"],
                          variable=cat_var, width=280,
                          fg_color=BLUE_BTN, button_color=BTN_ACTIVE,
                          corner_radius=12).pack(pady=8)

        def save():
            if not self.db_conn:
                messagebox.showerror("Error", "Database not connected!")
                return
            try:
                cur = self.db_conn.cursor()
                cur.execute(
                    "INSERT INTO Vault_Entry (Service, Username, Password, CategoryID) "
                    "VALUES (?, ?, ?, (SELECT CategoryID FROM Category WHERE Name = ?))",
                    (service_in.get(), user_in.get(), pass_in.get(), cat_var.get())
                )
                self.db_conn.commit()
                database.log_vault_action(self.db_conn, cur.lastrowid, "ADD_ENTRY")
                win.destroy()
                self.load_vault_data("All")
            except Exception as e:
                messagebox.showerror("Database Error", f"Could not save: {e}")

        ctk.CTkButton(inner, text="Save",
                      command=save, fg_color=GREEN_BTN,
                      hover_color="#1e7e34", corner_radius=16,
                      width=280, height=40,
                      font=("Helvetica", 14, "bold")).pack(pady=16)


    # ── LOAD VAULT DATA ───────────────────────────────────────────────────────
    def load_vault_data(self, category="All"):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        if not self.db_conn:
            return
        cur = self.db_conn.cursor()
        if category == "All":
            cur.execute("SELECT EntryID, Service, Username, Password FROM Vault_Entry")
        else:
            cur.execute(
                "SELECT v.EntryID, v.Service, v.Username, v.Password "
                "FROM Vault_Entry v "
                "JOIN Category c ON v.CategoryID = c.CategoryID "
                "WHERE c.Name = ?", (category,)
            )
        for idx, row in enumerate(cur.fetchall()):
            self.create_password_row(row, idx)


if __name__ == "__main__":
    app = SecVaultApp()
    app.mainloop()