import ctypes
import tkinter as tk
from PIL import Image, ImageTk
import platform
import re
import os
from tkinter import scrolledtext, filedialog, messagebox, ttk

from modulos.utils import check_attempts, register_failed_attempt, reset_attempts
from modulos.encryption import derive_key, save_encrypted, open_encrypted, ask_password, Fernet
from modulos.detect_dark_mode import detect_dark_mode

# DPI configuration to improve resolution on high-density screens
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Function to detect system dark mode


# Color configuration depending on system mode
dark_mode = detect_dark_mode()
bg_color = "#2e2e2e" if dark_mode else "#f4f4f4"
fg_color = "#ffffff" if dark_mode else "#000000"
text_bg_color = "#1e1e1e" if dark_mode else "#ffffff"
text_fg_color = "#d4d4d4" if dark_mode else "#000000"
scrollbar_color = "#1e1e1e" if dark_mode else "#d4d4d4"
border_color = "#000000" if dark_mode else "#d4d4d4"
cursor_color = "white" if dark_mode else "black"
menu_bg_color = "#333333" if dark_mode else "#ffffff"
menu_fg_color = "#ffffff" if dark_mode else "#000000"
SCROLLBAR_WIDTH = 10  # Scrollbar width

# Create 'data' folder if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

# Create the main window
root = tk.Tk()
root.title("Encrypted Text Editor")
root.geometry("900x700")
root.state('zoomed')  # Maximize window on startup
root.config(bg=bg_color, padx=0, pady=0)

# Adjust UI scaling
root.tk.call('tk', 'scaling', 1.5)

# Set window icon
icon_path = os.path.join(os.path.dirname(__file__), "images/logo.jpg")
icon_image = Image.open(icon_path)
icon_photo = ImageTk.PhotoImage(icon_image)
root.iconphoto(False, icon_photo)

# Create text area with scrollbar
text_area_frame = tk.Frame(root, bg=bg_color, bd=2, relief="solid", highlightbackground=border_color, highlightcolor=border_color)
text_area_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

text_area = scrolledtext.ScrolledText(text_area_frame, wrap=tk.WORD, font=("Consolas", 12), bg=text_bg_color, fg=text_fg_color, bd=0, padx=5, pady=5, insertbackground=cursor_color, undo=True)
text_area.pack(expand=True, fill=tk.BOTH)

# Configure scrollbar color and width
style = ttk.Style()
style.theme_use('clam')
style.configure("Vertical.TScrollbar", background=scrollbar_color, troughcolor=scrollbar_color, bordercolor=border_color, arrowcolor=fg_color, width=SCROLLBAR_WIDTH)
style.configure("Horizontal.TScrollbar", background=scrollbar_color, troughcolor=scrollbar_color, bordercolor=border_color, arrowcolor=fg_color, width=SCROLLBAR_WIDTH)

# Variables to store the current file path and save state
current_file = None
encrypted_file = False
saved_changes = True

# Function to update window title
def update_title():
    update_save_status()

# Function to update save status in the UI
def update_save_status():
    file_name = os.path.basename(current_file) if current_file else "Untitled"
    if not saved_changes:
        file_name += " *"
    status_label.config(text="Saved" if saved_changes else "Unsaved changes")
    file_label.config(text=file_name)

# Function to mark unsaved changes
def mark_changes(event=None):
    global saved_changes
    saved_changes = False
    update_title()
    text_area.edit_modified(False)  # Reset text area modification state

# Function to save a regular file
def save_file():
    global current_file, saved_changes
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        return

    if current_file and not encrypted_file:
        try:
            with open(current_file, "w", encoding="utf-8") as f:
                f.write(content)
            saved_changes = True
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the file.\n{e}")
    else:
        save_file_as()

# Function to save a file as
def save_file_as():
    global current_file, saved_changes, encrypted_file
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        return

    file = filedialog.asksaveasfilename(
        initialdir=os.path.expanduser("~/Desktop"),
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file:
        try:
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            current_file = file
            encrypted_file = False
            saved_changes = True
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the file.\n{e}")

# Function to open a regular file
def open_file():
    global current_file, saved_changes, encrypted_file
    file = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, content)
            current_file = file
            encrypted_file = False
            saved_changes = True
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open the file.\n{e}")

# Function to close the current file
def close_file():
    global current_file, saved_changes, encrypted_file
    if messagebox.askyesno("Confirm", "Are you sure you want to close the current file? Unsaved changes will be lost."):
        text_area.delete("1.0", tk.END)
        current_file = None
        encrypted_file = False
        saved_changes = True
        update_title()

# Function to save an encrypted file
def save_encrypted_file():
    global current_file, saved_changes, encrypted_file
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        return

    if current_file and encrypted_file:
        try:
            password = ask_password(parent=text_area)
            if not password:
                return

            key = derive_key(password)
            fernet = Fernet(key)

            # Verify password before saving
            try:
                with open(current_file, "rb") as f:
                    encrypted_content = f.read()
                fernet.decrypt(encrypted_content)
            except Exception as e:
                messagebox.showerror("Error", "Incorrect password.")
                return

            encrypted_content = fernet.encrypt(content.encode())

            with open(current_file, "wb") as f:
                f.write(encrypted_content)
            saved_changes = True
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the encrypted file.\n{e}")
    else:
        save_encrypted_file_as()

# Function to save an encrypted file as
def save_encrypted_file_as():
    global current_file, saved_changes, encrypted_file
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        return

    file = filedialog.asksaveasfilename(
        initialdir="data",
        defaultextension=".enc",
        filetypes=[("Encrypted files", "*.enc"), ("All files", "*.*")]
    )
    if file:
        try:
            password = ask_password(parent=text_area)
            if not password:
                return

            key = derive_key(password)
            fernet = Fernet(key)
            encrypted_content = fernet.encrypt(content.encode())

            with open(file, "wb") as f:
                f.write(encrypted_content)
            current_file = file
            encrypted_file = True
            saved_changes = True
            update_title()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save the encrypted file.\n{e}")

# Function to open an encrypted file
def open_encrypted_file():
    global current_file, saved_changes, encrypted_file
    file = filedialog.askopenfilename(
        initialdir="data",
        filetypes=[("Encrypted files", "*.enc"), ("All files", "*.*")]
    )
    if file:
        allowed, remaining_time = check_attempts(file)
        if not allowed:
            messagebox.showerror("Blocked", f"You have exceeded the number of attempts. Try again in {int(remaining_time // 3600)} hours and {int((remaining_time % 3600) // 60)} minutes.")
            return

        while True:
            password = ask_password(parent=text_area)
            if not password:
                return

            key = derive_key(password)
            fernet = Fernet(key)

            try:
                with open(file, "rb") as f:
                    encrypted_content = f.read()
                content = fernet.decrypt(encrypted_content).decode()
                text_area.delete("1.0", "end")
                text_area.insert("end", content)
                reset_attempts(file)  # Reset failed attempts on successful open
                current_file = file
                encrypted_file = True
                saved_changes = True
                update_title()
                messagebox.showinfo("Success", "Encrypted file opened successfully.")
                break
            except Exception as e:
                register_failed_attempt(file)  # Register failed attempt
                allowed, remaining_time = check_attempts(file)
                if not allowed:
                    messagebox.showerror("Blocked", f"You have exceeded the number of attempts. Try again in {int(remaining_time // 3600)} hours and {int((remaining_time % 3600) // 60)} minutes.")
                    return
                messagebox.showerror("Error", f"Incorrect password. Try again.\n{e}")

# Function to zoom in
def zoom_in(event=None):
    current_font_size = text_area.cget("font").split()[1]
    new_font_size = int(current_font_size) + 2
    text_area.config(font=("Consolas", new_font_size))

# Function to zoom out
def zoom_out(event=None):
    current_font_size = text_area.cget("font").split()[1]
    new_font_size = int(current_font_size) - 2
    text_area.config(font=("Consolas", new_font_size))

# Function to undo a change
def undo_change(event=None):
    try:
        text_area.edit_undo()
    except tk.TclError:
        pass

# Create the menu
menu_bar = tk.Menu(root, bg=bg_color, fg=fg_color)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0, bg=bg_color, fg=fg_color)
menu_bar.add_cascade(label="File", menu=file_menu)

file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Open Encrypted File", command=open_encrypted_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save As", command=save_file_as)
file_menu.add_separator()
file_menu.add_command(label="Save As (Encrypted)", command=save_encrypted_file_as)
file_menu.add_command(label="Save Encrypted File", command=save_encrypted_file)
file_menu.add_separator()
file_menu.add_command(label="Close File", command=close_file)
file_menu.add_command(label="Exit", command=root.quit)

# Create frame to display save status and file name
status_frame = tk.Frame(root, bg=bg_color)
status_frame.pack(fill=tk.X, padx=10, pady=5)

# Create label to display save status
status_label = tk.Label(status_frame, text="", bg=bg_color, fg=fg_color, anchor="w")
status_label.pack(side=tk.LEFT)

# Create label to display file name
file_label = tk.Label(status_frame, text="Untitled", bg=bg_color, fg=fg_color, anchor="e")
file_label.pack(side=tk.RIGHT)

# Bind Ctrl+S to save the file
root.bind('<Control-s>', lambda event: save_file() if not encrypted_file else save_encrypted_file())

# Bind Ctrl+ to zoom in
root.bind('<Control-=>', zoom_in)
root.bind('<Control-KP_Add>', zoom_in)

# Bind Ctrl- to zoom out
root.bind('<Control-minus>', zoom_out)
root.bind('<Control-KP_Subtract>', zoom_out)

# Bind Ctrl+Z to undo a change
root.bind('<Control-z>', undo_change)

# Bind text area modification event
text_area.bind("<<Modified>>", mark_changes)

# Run the application
root.mainloop()
