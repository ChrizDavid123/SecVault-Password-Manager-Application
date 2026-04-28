import os
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image
import database
import authentication
import passforge
import json

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

    # ── helpers ───────────────────────────────────────────────────────────────
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

        # Eye buttons
        for container, entry in [(c1, self.new_pw), (c2, self.confirm_pw)]:
            e = entry
            def _toggle(en=e, btn_ref=[None]):
                if en.cget("show") == "*":
                    en.configure(show="")
                    if btn_ref[0]: btn_ref[0].configure(text="🔒")
                else:
                    en.configure(show="*")
                    if btn_ref[0]: btn_ref[0].configure(text="👁️")
            b = ctk.CTkButton(container, text="👁️", width=30, height=30,
                              fg_color="transparent", text_color="#318ba2",
                              font=("Arial", 16), command=_toggle)
            b.pack(side="right", padx=4)
            # Wire the button reference so toggle can update it
            def _make_toggle(en, btn):
                def _t():
                    if en.cget("show") == "*":
                        en.configure(show="")
                        btn.configure(text="🔒")
                    else:
                        en.configure(show="*")
                        btn.configure(text="👁️")
                return _t
            b.configure(command=_make_toggle(e, b))

        self.setup_error = ctk.CTkLabel(card, text="", text_color=RED_BTN,
                                        font=("Helvetica", 11))
        self.setup_error.pack(pady=(6, 0))

        def save_master():
            p1, p2 = self.new_pw.get(), self.confirm_pw.get()
            # if len(p1) < 8:
            #     self.setup_error.configure(text="Password must be at least 8 characters!")
            #     return
            if p1 != p2:
                self.setup_error.configure(text="Passwords do not match!")
                return
            key = authentication.store_key(p1)
            self.db_conn = database.initialize_database(key)
            messagebox.showinfo("Success", "Master password set!")

            # Redirect to main window after create master password
            self.main_window()

        ctk.CTkButton(card, text="Save", corner_radius=20, width=140, height=38,
                      fg_color=BLUE_BTN, hover_color=BTN_HOVER,
                      font=("Helvetica", 14, "bold"), command=save_master).pack(pady=16)

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

        self.pw_entry = ctk.CTkEntry(entry_row, placeholder_text="Enter Key", show="*",
                                     height=40, border_width=0, fg_color=WHITE, text_color=TEXT_DARK)
        self.pw_entry.pack(side="left", padx=(14, 0), fill="x", expand=True)

        def toggle_pw():
            if self.pw_entry.cget("show") == "*":
                self.pw_entry.configure(show="")
                eye_btn.configure(text="🔒")
            else:
                self.pw_entry.configure(show="*")
                eye_btn.configure(text="👁️")

        eye_btn = ctk.CTkButton(entry_row, text="👁️", width=34, height=34,
                                corner_radius=17, fg_color="transparent",
                                text_color="#318ba2", hover_color="#EEEEEE",
                                font=("Arial", 14), command=toggle_pw)
        eye_btn.pack(side="right", padx=6)

        ctk.CTkButton(card, text="Enter", corner_radius=14, width=120, height=36,
                      fg_color=BLUE_BTN, hover_color=BTN_HOVER,
                      font=("Helvetica", 13, "bold"),
                      command=self.handle_login).pack(pady=16)

        link = ctk.CTkLabel(card, text="First Time?  Set Up Master Password",
                            font=("Helvetica", 11, "underline"),
                            cursor="hand2", text_color="#1a4a7a")
        link.pack(pady=4)
        link.bind("<Button-1>", lambda _: self.show_first_time_setup())

    def handle_login(self):
        password = self.pw_entry.get()
        if not password or not password.strip():
            messagebox.showwarning("Input Error", "Please enter your master password.")
        try:
            key = authentication.verify_key(password)
            conn = database.access_database(key)

            self.db_conn = conn
            self.main_window()
        except Exception:
            messagebox.showerror("Error", "Master password is invalid!")

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

        # Lock Vault (bottom)
        ctk.CTkButton(sidebar, text="↪  Lock Vault",
                      fg_color="transparent", text_color=TEXT_LIGHT,
                      font=("Helvetica", 13, "bold"),
                      hover_color=BTN_HOVER,
                      command=self.show_lock_window).pack(side="bottom", pady=22)

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
        def toggle_view():
            if "·" in pw_label.cget("text"):
                pw_label.configure(text=f"{data[1]}   {data[3]}")
                view_btn.configure(text="🔒")
            else:
                pw_label.configure(text=masked)
                view_btn.configure(text="👁️")

        view_btn = ctk.CTkButton(bar, text="👁️", width=26, height=26,
                                 fg_color="transparent", text_color="#318ba2",
                                 font=("Arial", 13), hover_color="#eaf4ff",
                                 command=toggle_view)
        view_btn.pack(side="right", padx=2)

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

        def update_p():
            new_p = simpledialog.askstring("Update", f"New password for {data[1]}:", parent=win)
            if new_p:
                cur = self.db_conn.cursor()
                cur.execute("UPDATE Vault_Entry SET Password = ? WHERE EntryID = ?",
                            (new_p, data[0]))
                self.db_conn.commit()
                win.destroy()
                self.load_vault_data("All")

        def delete_p():
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
                      command=update_p).pack(pady=(18, 8), padx=18, fill="x")

        ctk.CTkButton(frame, text="Delete",
                      fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
                      hover_color=RED_BTN, corner_radius=16,
                      height=36, font=("Helvetica", 13, "bold"),
                      command=delete_p).pack(pady=(0, 8), padx=18, fill="x")

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

        # Master password row
        pw_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        pw_row.pack(pady=(38, 10), padx=28, anchor="w")

        ctk.CTkLabel(pw_row, text="Current Master Password",
                     font=("Helvetica", 13), text_color=TEXT_DARK).pack(side="left", padx=(0, 10))

        pw_cont = ctk.CTkFrame(pw_row, fg_color=WHITE,
                               corner_radius=10, width=280, height=34)
        pw_cont.pack_propagate(False)
        pw_cont.pack(side="left")

        pw_display = ctk.CTkEntry(pw_cont, show="*", border_width=0,
                                  fg_color=WHITE, text_color=TEXT_DARK, width=230)
        
        # pw_display.insert(0, self.current_master_password) This is a fatal security vulnerability
        pw_display.configure(state="readonly")
        pw_display.pack(side="left", padx=(10, 0), fill="x", expand=True)

        # def toggle_pw():
        #     if pw_display.cget("show") == "*":
        #         pw_display.configure(show="")
        #         eye_btn.configure(text="🔒")
        #     else:
        #         pw_display.configure(show="*")
        #         eye_btn.configure(text="👁️")

        # eye_btn = ctk.CTkButton(pw_cont, text="👁️", width=26, height=26,
        #                         fg_color="transparent", text_color="#318ba2",
        #                         font=("Arial", 13), hover_color="#eaf4ff" ,command=toggle_pw)
        # eye_btn.pack(side="right", padx=4)

        # Three dots → change/delete popup
        def show_pw_options():
            opt = ctk.CTkToplevel(win)
            opt.title("")
            opt.geometry("210x160")
            opt.resizable(0, 0)
            opt.attributes("-topmost", True)
            self._popup_icon(opt)

            opt_frame = ctk.CTkFrame(opt, fg_color=BG_POPUP, corner_radius=14)
            opt_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # def change_master():
        #     new_pw = simpledialog.askstring("Change Password",
        #                                     "Enter new master password:",
        #                                     show="*", parent=win)
        #     if new_pw:
        #         # if len(new_pw):
        #         #     messagebox.showwarning("Too Short",
        #         #                            "Must be at least 8 characters!", parent=win)
        #         #     return
        #         authentication.store_key(new_pw)
        #         self.current_master_password = new_pw
        #         messagebox.showinfo("Success", "Master password updated!", parent=win)
        #         opt.destroy()

        def delete_account():
            if messagebox.askyesno("Confirm Delete",
                                    "Delete ALL data permanently?", parent=win):
                
                with open("auth_store.json", "w") as f:
                    json.dump({}, f)
                # if self.db_conn:
                #     self.db_conn.close()

                # Delete database
                database.delete_vault(self.db_conn)

                # opt.destroy()
                win.destroy()

                # Show first time setup window
                self.show_first_time_setup()

            # ctk.CTkButton(opt_frame, text="Change / Update",
            #               fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
            #               hover_color=BTN_HOVER, corner_radius=16,
            #               height=36, font=("Helvetica", 13, "bold"),
            #               command=change_master).pack(pady=(18, 8), padx=16, fill="x")

            # ctk.CTkButton(opt_frame, text="Delete",
            #               fg_color=BTN_IDLE, text_color=TEXT_LIGHT,
            #               hover_color=RED_BTN, corner_radius=16,
            #               height=36, font=("Helvetica", 13, "bold"),
            #               command=delete_account).pack(pady=(0, 8), padx=16, fill="x")

        ctk.CTkButton(pw_row, text="⋮", width=24, fg_color="transparent",
                      text_color=TEXT_DARK, font=("Arial", 20),
                      hover_color="#cce0f0",
                      command=show_pw_options).pack(side="left", padx=6)

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
            e = ctk.CTkEntry(inner, placeholder_text=placeholder, width=280,
                             height=36, corner_radius=10,
                             fg_color=WHITE, border_width=0,
                             text_color=TEXT_DARK)
            e.pack(pady=6)
            return e

        service_in = _entry("Service")
        user_in    = _entry("Username")
        pass_in    = _entry("Password")

        def gen():
            new_p = passforge.password_generator()
            pass_in.delete(0, "end")
            pass_in.insert(0, new_p)

        ctk.CTkButton(inner, text="⚡  Generate Strong Password",
                      command=gen, fg_color="#4a4a6a",
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