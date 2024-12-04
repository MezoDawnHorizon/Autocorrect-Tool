import sys
import json
import os
import tkinter as tk
from tkinter import messagebox
import keyboard
import pystray
from pystray import MenuItem as item
from PIL import Image
import threading
import winreg as reg

# Load or initialize the corrections
corrections_file = "corrections.json"
try:
    with open(corrections_file, "r") as file:
        corrections = json.load(file)
except FileNotFoundError:
    corrections = {}
    with open(corrections_file, "w") as file:
        json.dump(corrections, file, indent=4)

# Save corrections to the file
def save_corrections():
    with open(corrections_file, "w") as file:
        json.dump(corrections, file, indent=4)

# Function to handle the exit action
def exit_action(icon, item):
    icon.stop()
    sys.exit()

# Autocorrect function
current_word = ""
def autocorrect(event):
    global current_word
    if event.name == "space":
        if current_word in corrections:
            corrected_word = corrections[current_word]
            for _ in range(len(current_word) + 1):
                keyboard.send("backspace")
            keyboard.write(corrected_word + " ")
        current_word = ""
    elif event.name == "backspace" and current_word:
        current_word = current_word[:-1]
    elif len(event.name) == 1 and event.name.isprintable():
        current_word += event.name

# Manage corrections window
def manage_corrections():
    def add_correction():
        mistake = mistake_entry.get().strip()
        correction = correction_entry.get().strip()
        if mistake and correction:
            corrections[mistake] = correction
            save_corrections()
            update_listbox()
            mistake_entry.delete(0, tk.END)
            correction_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Both fields are required.")

    def remove_correction():
        selected = listbox.curselection()
        if selected:
            selected_item = listbox.get(selected[0])
            mistake = selected_item.split(" -> ")[0]
            if mistake in corrections:
                del corrections[mistake]
                save_corrections()
                update_listbox()
                messagebox.showinfo("Success", f"Removed: {selected_item}")
            else:
                messagebox.showerror("Error", f"'{mistake}' not found in corrections.")
        else:
            messagebox.showerror("Error", "Select a correction to remove.")

    def update_listbox():
        listbox.delete(0, tk.END)
        for mistake, correction in sorted(corrections.items()):
            listbox.insert(tk.END, f"{mistake} -> {correction}")

    def add_to_startup():
        exe_path = os.path.abspath("Autocorrect Tool")
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "AutocorrectTool", 0, reg.REG_SZ, exe_path)
            reg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable startup: {e}")

    def remove_from_startup():
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "AutocorrectTool")
            reg.CloseKey(key)
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable startup: {e}")

    def toggle_startup():
        if startup_var.get():
            add_to_startup()
        else:
            remove_from_startup()

    window = tk.Tk()
    window.title("Manage Autocorrections")
    window.geometry("400x420")
    window.resizable(False, False)

    listbox = tk.Listbox(window, width=50, height=10)
    listbox.pack(pady=10)
    update_listbox()

    mistake_label = tk.Label(window, text="Mistake:")
    mistake_label.pack()
    mistake_entry = tk.Entry(window)
    mistake_entry.pack()

    correction_label = tk.Label(window, text="Correction:")
    correction_label.pack()
    correction_entry = tk.Entry(window)
    correction_entry.pack()

    add_button = tk.Button(window, text="Add Correction", command=add_correction)
    add_button.pack(pady=5)

    remove_button = tk.Button(window, text="Remove Correction", command=remove_correction)
    remove_button.pack(pady=5)

    startup_var = tk.BooleanVar()
    startup_checkbox = tk.Checkbutton(window, text="Run at Startup", variable=startup_var, command=toggle_startup)
    startup_checkbox.pack(pady=10)

    close_button = tk.Button(window, text="Close", command=window.destroy)
    close_button.pack(pady=5)

    window.mainloop()

# Create the tray icon
def create_image():
    return Image.open("icon.png")

def setup_tray():
    def open_manage_corrections():
        threading.Thread(target=manage_corrections, daemon=True).start()

    icon = pystray.Icon("Autocorrect")
    icon.icon = create_image()
    icon.title = "Autocorrect Tool"
    icon.menu = pystray.Menu(
        item('Manage Corrections', lambda: open_manage_corrections()),
        item('Exit', exit_action)
    )
    keyboard.on_press(autocorrect)
    icon.run()

# Start the application
setup_tray()
