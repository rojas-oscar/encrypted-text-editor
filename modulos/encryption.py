from tkinter import simpledialog, messagebox, filedialog, Toplevel, Label, Entry, Button, Frame
from cryptography.fernet import Fernet
import base64
import hashlib
import time
import json
import os

# Path to the file for storing failed attempts
ATTEMPTS_PATH = "data/attempts_state.json"

# Load failed attempts from the file
def load_attempts_state():
    if os.path.exists(ATTEMPTS_PATH):
        with open(ATTEMPTS_PATH, "r") as f:
            return json.load(f)
    return {}

# Save failed attempts to the file
def save_attempts_state(state):
    with open(ATTEMPTS_PATH, "w") as f:
        json.dump(state, f)

# Check if the user is blocked for a specific file
def check_attempts(file):
    state = load_attempts_state()
    if file in state:
        attempts, last_attempt = state[file]
        if attempts >= 3 and time.time() - last_attempt < 86400:
            return False, 86400 - (time.time() - last_attempt)
    return True, 0

# Register a failed attempt for a specific file
def register_failed_attempt(file):
    state = load_attempts_state()
    if file in state:
        state[file][0] += 1
        state[file][1] = time.time()
    else:
        state[file] = [1, time.time()]
    save_attempts_state(state)

# Reset failed attempts for a specific file
def reset_attempts(file):
    state = load_attempts_state()
    if file in state:
        del state[file]
    save_attempts_state(state)

# Derive a consistent key from the password using SHA-256 and convert it to base64
def derive_key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

# Custom interface to ask for a password
def ask_password(title="Password", prompt="Enter the password:", show="*", width=30, parent=None):
    password = None

    # Dialog box dimensions
    dialog_width = 300  # Width of the main window
    dialog_height = 150  # Height of the main window

    # Button dimensions
    button_width = 12  # Width of the buttons
    button_height = 1  # Height of the buttons

    def accept(event=None):  # The `event` parameter allows it to be called from a keyboard event
        nonlocal password
        password = entry.get()
        dialog.destroy()

    def cancel():
        nonlocal password
        password = None
        dialog.destroy()

    # Create dialog window
    dialog = Toplevel(parent)
    dialog.title(title)

    # Center the dialog box on the screen
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x_position = (screen_width // 2) - (dialog_width // 2)
    y_position = (screen_height // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x_position}+{y_position}")

    dialog.transient(parent)
    dialog.grab_set()

    # Dialog box widgets
    Label(dialog, text=prompt).pack(pady=(10, 5))
    entry = Entry(dialog, show=show, width=width)
    entry.pack(padx=10, pady=5)
    entry.focus_set()

    # Bind the Enter key to the Accept button
    entry.bind("<Return>", accept)

    # Accept and Cancel buttons
    button_frame = Frame(dialog)  # Frame to center the buttons
    button_frame.pack(pady=10)

    Button(button_frame, text="Accept", width=button_width, height=button_height, command=accept).pack(side="left", padx=5)
    Button(button_frame, text="Cancel", width=button_width, height=button_height, command=cancel).pack(side="left", padx=5)

    # Wait for user interaction
    parent.wait_window(dialog)
    return password

# Function to save an encrypted file
def save_encrypted(text_area):
    content = text_area.get("1.0", "end-1c")
    if not content:
        messagebox.showinfo("Information", "There is nothing to save.")
        return

    password = ask_password(parent=text_area)
    if not password:
        return

    key = derive_key(password)
    fernet = Fernet(key)
    encrypted_content = fernet.encrypt(content.encode())

    file = filedialog.asksaveasfilename(
        initialdir="data",
        defaultextension=".enc",
        filetypes=[("Encrypted files", "*.enc"), ("All files", "*.*")]
    )
    if file:
        with open(file, "wb") as f:
            f.write(encrypted_content)
        messagebox.showinfo("Success", "Encrypted file saved successfully.")

# Function to open an encrypted file
def open_encrypted(text_area):
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
                messagebox.showinfo("Success", "Encrypted file opened successfully.")
                break
            except Exception as e:
                register_failed_attempt(file)  # Register failed attempt
                allowed, remaining_time = check_attempts(file)
                if not allowed:
                    messagebox.showerror("Blocked", f"You have exceeded the number of attempts. Try again in {int(remaining_time // 3600)} hours and {int((remaining_time % 3600) // 60)} minutes.")
                    return
                messagebox.showerror("Error", f"Incorrect password. Try again.\n{e}")
