# -- YOU CAN CREATE A CUSTOM THEME BASED OFF THE CUSTOME CTHEME FILE I PROVIDED --

import customtkinter
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import json
import os
import uuid
from datetime import datetime
import ast  # For safely evaluating Python-like syntax
import requests  # Import for update functionality

def check_for_updates(current_file_path):
    """
    Checks for updates to the Todo Python script from GitHub.

    Args:
        current_file_path (str): The absolute path to the current Todo Python.py file.
    """
    check_url = "https://raw.githubusercontent.com/SosoTlm/todo-python/refs/heads/main/Todo%20Python.py"
    download_url_raw = "https://raw.githubusercontent.com/SosoTlm/todo-python/main/Todo%20Python.py"

    try:
        print("Checking for Todo-Python Updates, please wait...")
        response = requests.get(check_url)
        response.raise_for_status()  # Raise an exception for bad status codes
        latest_code = response.text

        with open(current_file_path, 'r', encoding='utf-8') as f:
            current_code = f.read()

        if latest_code != current_code:
            print("A code update is available.")
            install = input("Do you want to install the update now? (yes/no): ").lower()
            if install == 'yes':
                print("Downloading the new version...")
                download_response = requests.get(download_url_raw)
                download_response.raise_for_status()
                updated_code = download_response.text

                try:
                    os.remove(current_file_path)
                    with open(current_file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_code)
                    print("Update installed successfully! Please restart the application.")
                except Exception as e:
                    print(f"Error while nstalling the update: {e}")
            else:
                print("Update installation skipped.")
        else:
            print("Your code is already up to date.")

    except requests.exceptions.RequestException as e:
        print(f"Error while checking for updates: {e}")
    except FileNotFoundError:
        print(f"Error: Current file has not been found at {current_file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Constants ---
DATA_FILE = "kanban_tasks.json"
STATUSES = ["Todo", "InProgress", "Done"]
PRIORITIES = ["Low", "Important", "Urgent"]
VERSION = "0.1.0"
DEFAULT_THEMES = ["System", "Dark", "Light"]

# --- Helper function to read and parse ctheme file ---
def parse_ctheme_file(filepath):
    theme_data = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value_str = line.split("=", 1)
                    key = key.strip()
                    value_str = value_str.strip()
                    try:
                        theme_data[key] = ast.literal_eval(value_str)
                    except (ValueError, SyntaxError):
                        theme_data[key] = value_str
    except FileNotFoundError:
        tkinter.messagebox.showerror("Error", f"Theme file not found: {filepath}")
        return None
    return theme_data

# --- Function to apply a custom theme ---
def apply_custom_theme(app, theme_data):
    if not theme_data:
        return

    if 'BACKCOLOR' in theme_data:
        try:
            bg_color = theme_data['BACKCOLOR']
            app.configure(bg=f'rgb{bg_color}')
            for frame in [app.todo_frame, app.inprogress_frame, app.done_frame, app.button_frame]:
                frame.configure(fg_color=bg_color)
            app.update_board()
        except Exception as e:
            print(f"Error applying BACKCOLOR: {e}")

    if 'BACKCOLOR.GRADIENT' in theme_data:
        gradient_str = theme_data['BACKCOLOR.GRADIENT']
        print(f"Gradient not yet implemented: {gradient_str}") # Placeholder

    if 'CUSTOM.STATUSES' in theme_data:
        custom_statuses = theme_data['CUSTOM.STATUSES']
        global STATUSES
        STATUSES = DEFAULT_THEMES + custom_statuses # Update global statuses
        app.update_board() # Re-render might be needed if statuses affect layout

# --- Task Structure (using dictionary) ---
def create_task(title, description, status="todo", priority="medium", due_date=None):
    if status not in STATUSES:
        print(f"Warning: Invalid status '{status}'. Defaulting to 'todo'.")
        status = "Todo"
    if priority not in PRIORITIES:
        print(f"Warning: Invalid priority '{priority}'. Defaulting to 'medium'.")
        priority = "Important"
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

# --- Data Persistence ---
def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            tasks = json.load(f)
            if not isinstance(tasks, list):
                print(f"Warning: Data file '{DATA_FILE}' does not contain a list. Starting fresh.")
                return []
            return tasks
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading tasks from {DATA_FILE}: {e}")
        return []

def save_tasks(tasks):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(tasks, f, indent=4)
    except IOError as e:
        print(f"Error saving tasks to {DATA_FILE}: {e}")

# --- Core Functions (modified for customtkinter) ---
# We'll need to adapt these to interact with the GUI elements.

class TaskFrame(customtkinter.CTkFrame):
    def __init__(self, master, task, app, **kwargs):
        super().__init__(master, **kwargs)
        self.task = task
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.title_label = customtkinter.CTkLabel(self, text=task['title'], font=customtkinter.CTkFont(size=14, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="ew")
        self.priority_label = customtkinter.CTkLabel(self, text=f"Priority: {task['priority'].capitalize()}", fg_color=self._get_priority_color(task['priority']))
        self.priority_label.grid(row=1, column=0, padx=5, pady=(0, 5), sticky="ew")
        self.bind("<Button-1>", self.show_details)
        self.bind("<Button-3>", self.show_context_menu) # Bind right-click

        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_task)
        self.context_menu.add_command(label="Remove", command=self.remove_task)

    def _get_priority_color(self, priority):
        if priority == 'Urgent':
            return "red"
        elif priority == 'Important':
            return "yellow"
        else:
            return "green"

    def show_details(self, event):
        EditTaskDialog(self.app, self.task)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def edit_task(self):
        EditTaskDialog(self.app, self.task)

    def remove_task(self):
        if tkinter.messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove '{self.task['title']}'?"):
            self.app.tasks.remove(self.task)
            self.app.update_board()
            save_tasks(self.app.tasks)

class AddTaskDialog(customtkinter.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.title("Add New Task")
        self.geometry("400x300")
        self.resizable(False, False)

        self.title_label = customtkinter.CTkLabel(self, text="Title:")
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.title_entry = customtkinter.CTkEntry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.description_label = customtkinter.CTkLabel(self, text="Description:")
        self.description_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.description_entry = customtkinter.CTkTextbox(self, height=50)
        self.description_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.priority_label = customtkinter.CTkLabel(self, text="Priority:")
        self.priority_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.priority_menu = customtkinter.CTkOptionMenu(self, values=PRIORITIES)
        self.priority_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set("medium")

        self.due_date_label = customtkinter.CTkLabel(self, text="Due Date (YYYY-MM-DD):")
        self.due_date_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.due_date_entry = customtkinter.CTkEntry(self)
        self.due_date_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status:")
        self.status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.status_menu = customtkinter.CTkOptionMenu(self, values=STATUSES)
        self.status_menu.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.status_menu.set("todo")

        self.add_button = customtkinter.CTkButton(self, text="Add Task", command=self.add_task)
        self.add_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus()
        self.grab_set()

    def add_task(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("0.0", "end").strip()
        priority = self.priority_menu.get()
        due_date = self.due_date_entry.get().strip()
        status = self.status_menu.get()

        if not title:
            tkinter.messagebox.showerror("Error", "Title cannot be empty.")
            return

        new_task = create_task(title, description, status, priority, due_date)
        self.master.tasks.append(new_task)
        self.master.update_board()
        save_tasks(self.master.tasks)
        self.destroy()

class EditTaskDialog(customtkinter.CTkToplevel):
    def __init__(self, master, task, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.task = task
        self.title(f"Edit Task: {task['title']}")
        self.geometry("400x350")
        self.resizable(False, False)

        self.title_label = customtkinter.CTkLabel(self, text="Title:")
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.title_entry = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(value=task['title']))
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.description_label = customtkinter.CTkLabel(self, text="Description:")
        self.description_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.description_entry = customtkinter.CTkTextbox(self, height=50)
        self.description_entry.insert("0.0", task['description'])
        self.description_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.priority_label = customtkinter.CTkLabel(self, text="Priority:")
        self.priority_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.priority_menu = customtkinter.CTkOptionMenu(self, values=PRIORITIES)
        self.priority_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set(task['priority'])

        self.due_date_label = customtkinter.CTkLabel(self, text="Due Date (YYYY-MM-DD):")
        self.due_date_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.due_date_entry = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(value=task.get('due_date', '')))
        self.due_date_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status:")
        self.status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.status_menu = customtkinter.CTkOptionMenu(self, values=STATUSES, command=self.status_changed)
        self.status_menu.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.status_menu.set(task['status'])

        self.move_back_button = customtkinter.CTkButton(self, text="Move Back", command=self.move_back)
        self.move_back_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.move_forward_button = customtkinter.CTkButton(self, text="Move Forward", command=self.move_forward)
        self.move_forward_button.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        self.save_button = customtkinter.CTkButton(self, text="Save Changes", command=self.save_changes)
        self.save_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        self.delete_button = customtkinter.CTkButton(self, text="Delete Task", fg_color="darkred", hover_color="red", command=self.delete_task)
        self.delete_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        self._update_move_button_state()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus()
        self.grab_set()

    def save_changes(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("0.0", "end").strip()
        priority = self.priority_menu.get()
        due_date = self.due_date_entry.get().strip()
        status = self.status_menu.get()

        if not title:
            tkinter.messagebox.showerror("Error", "Title cannot be empty.")
            return

        self.task['title'] = title
        self.task['description'] = description
        self.task['priority'] = priority
        self.task['due_date'] = due_date if due_date else None
        self.task['status'] = status
        self.task['updated_at'] = datetime.now().isoformat()
        self.master.update_board()
        save_tasks(self.master.tasks)
        self.destroy()

    def delete_task(self):
        if tkinter.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.task['title']}'?"):
            self.master.tasks.remove(self.task)
            self.master.update_board()
            save_tasks(self.master.tasks)
            self.destroy()

    def move_forward(self):
        current_status_index = STATUSES.index(self.task['status'])
        if current_status_index < len(STATUSES) - 1:
            self.task['status'] = STATUSES[current_status_index + 1]
            self.task['updated_at'] = datetime.now().isoformat()
            self.master.update_board()
            save_tasks(self.master.tasks)
            self._update_move_button_state()

    def move_back(self):
        current_status_index = STATUSES.index(self.task['status'])
        if current_status_index > 0:
            self.task['status'] = STATUSES[current_status_index - 1]
            self.task['updated_at'] = datetime.now().isoformat()
            self.master.update_board()
            save_tasks(self.master.tasks)
            self._update_move_button_state()

    def status_changed(self, new_status):
        self._update_move_button_state()

    def _update_move_button_state(self):
        current_status_index = STATUSES.index(self.task['status'])
        self.move_back_button.configure(state="normal" if current_status_index > 0 else "disabled")
        self.move_forward_button.configure(state="normal" if current_status_index < len(STATUSES) - 1 else "disabled")

class SettingsDialog(customtkinter.CTkToplevel):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.app = app
        self.title("Settings")
        self.geometry("300x300") # Increased height
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Theme label
        self.grid_rowconfigure(1, weight=0) # Theme menu
        self.grid_rowconfigure(2, weight=0) # Load custom button
        self.grid_rowconfigure(3, weight=1) # Spacer for dynamic buttons
        self.grid_rowconfigure(4, weight=0) # Version label

        self.theme_label = customtkinter.CTkLabel(self, text="Theme:")
        self.theme_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")

        self.theme_menu_values = DEFAULT_THEMES[:] # Start with default themes
        self.theme_menu = customtkinter.CTkOptionMenu(self, values=self.theme_menu_values, command=self.change_theme)
        self.theme_menu.set(customtkinter.get_appearance_mode())
        self.theme_menu.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.load_custom_theme_button = customtkinter.CTkButton(self, text="Add Custom Theme File", command=self.load_custom_theme_file)
        self.load_custom_theme_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.version_label = customtkinter.CTkLabel(self, text=f"Build: Beta 0.332.1")
        self.version_label.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="w")

        self.custom_theme_buttons_frame = customtkinter.CTkFrame(self)
        self.custom_theme_buttons_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.custom_theme_buttons_frame.grid_columnconfigure(0, weight=1)

        self.loaded_custom_themes = {} # Store loaded theme data and names
        self.update_theme_menu()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus()
        self.grab_set()

    def change_theme(self, theme):
        if theme in ["Dark", "Light", "System"]:
            customtkinter.set_appearance_mode(theme)
            customtkinter.set_default_color_theme("blue") # Reset default color theme
            self.app.update_board()
        elif theme in self.loaded_custom_themes:
            apply_custom_theme(self.app, self.loaded_custom_themes[theme])

    def load_custom_theme_file(self):
        filepath = customtkinter.filedialog.askopenfilename(
            title="Select Custom Theme File",
            filetypes=[("Custom Theme", "*.ctheme")]
        )
        if filepath:
            theme_data = parse_ctheme_file(filepath)
            if theme_data and theme_data.get('ADD_TO_MENU') == True and 'MENU_NAME' in theme_data:
                menu_name = theme_data['MENU_NAME']
                if menu_name not in self.loaded_custom_themes:
                    self.loaded_custom_themes[menu_name] = theme_data
                    self.update_theme_menu()
                    tkinter.messagebox.showinfo("Info", f"Custom theme '{menu_name}' added to the theme menu.")
            elif theme_data:
                apply_custom_theme(self.app, theme_data) # Apply even if not added to menu
                tkinter.messagebox.showinfo("Info", "Custom theme loaded (applied directly).")
                self.app.update_board()
            else:
                tkinter.messagebox.showerror("Error", "Invalid custom theme file.")

    def update_theme_menu(self):
        self.theme_menu_values = DEFAULT_THEMES + list(self.loaded_custom_themes.keys())
        self.theme_menu.configure(values=self.theme_menu_values)
        # Keep the current selection if it's still valid
        current_theme = self.theme_menu.get()
        if current_theme not in self.theme_menu_values:
            self.theme_menu.set(customtkinter.get_appearance_mode())

# --- Modifications needed in AddTaskDialog and EditTaskDialog for custom statuses ---
class AddTaskDialog(customtkinter.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.title("Add A New ToDo-Task")
        self.geometry("400x300")
        self.resizable(False, False)

        self.title_label = customtkinter.CTkLabel(self, text="Title:")
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.title_entry = customtkinter.CTkEntry(self)
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.description_label = customtkinter.CTkLabel(self, text="Description:")
        self.description_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.description_entry = customtkinter.CTkTextbox(self, height=50)
        self.description_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.priority_label = customtkinter.CTkLabel(self, text="Priority:")
        self.priority_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.priority_menu = customtkinter.CTkOptionMenu(self, values=PRIORITIES)
        self.priority_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set("Important")

        self.due_date_label = customtkinter.CTkLabel(self, text="Due Date (YYYY-MM-DD):")
        self.due_date_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.due_date_entry = customtkinter.CTkEntry(self)
        self.due_date_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status:")
        self.status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.status_menu = customtkinter.CTkOptionMenu(self, values=STATUSES)
        self.status_menu.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.status_menu.set("Todo")

        self.add_button = customtkinter.CTkButton(self, text="Add Todo-Task", command=self.add_task)
        self.add_button.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus()
        self.grab_set()

    def add_task(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("0.0", "end").strip()
        priority = self.priority_menu.get()
        due_date = self.due_date_entry.get().strip()
        status = self.status_menu.get()

        if not title:
            tkinter.messagebox.showerror("Error", "Title cannot be empty.")
            return

        new_task = create_task(title, description, status, priority, due_date)
        self.master.tasks.append(new_task)
        self.master.update_board()
        save_tasks(self.master.tasks)
        self.destroy()

class EditTaskDialog(customtkinter.CTkToplevel):
    def __init__(self, master, task, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.task = task
        self.title(f"Edit Task: {task['title']}")
        self.geometry("400x350")
        self.resizable(False, False)

        self.title_label = customtkinter.CTkLabel(self, text="Title:")
        self.title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.title_entry = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(value=task['title']))
        self.title_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.description_label = customtkinter.CTkLabel(self, text="Description:")
        self.description_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.description_entry = customtkinter.CTkTextbox(self, height=50)
        self.description_entry.insert("0.0", task['description'])
        self.description_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.priority_label = customtkinter.CTkLabel(self, text="Priority:")
        self.priority_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.priority_menu = customtkinter.CTkOptionMenu(self, values=PRIORITIES)
        self.priority_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        self.priority_menu.set(task['priority'])

        self.due_date_label = customtkinter.CTkLabel(self, text="Due Date (YYYY-MM-DD):")
        self.due_date_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.due_date_entry = customtkinter.CTkEntry(self, textvariable=customtkinter.StringVar(value=task.get('due_date', '')))
        self.due_date_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.status_label = customtkinter.CTkLabel(self, text="Status:")
        self.status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.status_menu = customtkinter.CTkOptionMenu(self, values=STATUSES, command=self.status_changed)
        self.status_menu.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.status_menu.set(task['status'])

        self.move_back_button = customtkinter.CTkButton(self, text="Move Back", command=self.move_back)
        self.move_back_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        self.move_forward_button = customtkinter.CTkButton(self, text="Move Forward", command=self.move_forward)
        self.move_forward_button.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

        self.save_button = customtkinter.CTkButton(self, text="Save Changes", command=self.save_changes)
        self.save_button.grid(row=6, column=0, padx=10, pady=10, sticky="ew")
        self.delete_button = customtkinter.CTkButton(self, text="Delete Task", fg_color="darkred", hover_color="red", command=self.delete_task)
        self.delete_button.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        self._update_move_button_state()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus()
        self.grab_set()

    def save_changes(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get("0.0", "end").strip()
        priority = self.priority_menu.get()
        due_date = self.due_date_entry.get().strip()
        status = self.status_menu.get()

        if not title:
            tkinter.messagebox.showerror("Error", "Title cannot be empty.")
            return

        self.task['title'] = title
        self.task['description'] = description
        self.task['priority'] = priority
        self.task['due_date'] = due_date if due_date else None
        self.task['status'] = status
        self.task['updated_at'] = datetime.now().isoformat()
        self.master.update_board()
        save_tasks(self.master.tasks)
        self.destroy()

    def delete_task(self):
        if tkinter.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.task['title']}'?"):
            self.master.tasks.remove(self.task)
            self.master.update_board()
            save_tasks(self.master.tasks)
            self.destroy()

    def move_forward(self):
        current_status_index = STATUSES.index(self.task['status'])
        if current_status_index < len(STATUSES) - 1:
            self.task['status'] = STATUSES[current_status_index + 1]
            self.task['updated_at'] = datetime.now().isoformat()
            self.master.update_board()
            save_tasks(self.master.tasks)
            self._update_move_button_state()

    def move_back(self):
        current_status_index = STATUSES.index(self.task['status'])
        if current_status_index > 0:
            self.task['status'] = STATUSES[current_status_index - 1]
            self.task['updated_at'] = datetime.now().isoformat()
            self.master.update_board()
            save_tasks(self.master.tasks)
            self._update_move_button_state()

    def status_changed(self, new_status):
        self._update_move_button_state()

    def _update_move_button_state(self):
        current_status_index = STATUSES.index(self.task['status'])
        self.move_back_button.configure(state="normal" if current_status_index > 0 else "disabled")
        self.move_forward_button.configure(state="normal" if current_status_index < len(STATUSES) - 1 else "disabled")

class KanbanBoardApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Todo-Python: The lightweight ToDo Taksk Aplication")
        self.geometry("1000x650")
        self.grid_columnconfigure(len(STATUSES), weight=1)  # Adjust column configuration based on statuses
        self.tasks = load_tasks()

        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=0, column=0, columnspan=len(STATUSES), padx=20, pady=10, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.add_task_button = customtkinter.CTkButton(self.button_frame, text="Add New Task", command=self.show_add_task_dialog)
        self.add_task_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")

        self.settings_button = customtkinter.CTkButton(self.button_frame, text="Settings", command=self.show_settings_dialog)
        self.settings_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="ew")

        self.status_frames = {}
        self.status_scrollable_frames = {}

        for i, status in enumerate(STATUSES):
            frame = customtkinter.CTkFrame(self)
            frame.grid(row=1, column=i, padx=20, pady=10, sticky="nsew")
            label = customtkinter.CTkLabel(frame, text=status.capitalize(), font=customtkinter.CTkFont(size=18, weight="bold"))
            label.pack(padx=10, pady=10)
            scrollable_frame = customtkinter.CTkScrollableFrame(frame, label_text="")
            scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)
            self.status_frames[status] = frame
            self.status_scrollable_frames[status] = scrollable_frame

        self.update_board()

    def show_add_task_dialog(self):
        AddTaskDialog(self).mainloop()  # Ensure the dialog's status menu is updated on creation

    def show_settings_dialog(self):
        SettingsDialog(self, self)

    def update_board(self):
        global STATUSES

        # Destroy existing task frames
        for frame in self.status_scrollable_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()

        # Recreate columns if statuses have changed
        existing_statuses = list(self.status_frames.keys())
        if set(STATUSES) != set(existing_statuses):
            for status in existing_statuses:
                self.status_frames[status].destroy()
            self.status_frames = {}
            self.status_scrollable_frames = {}
            self.grid_columnconfigure(len(STATUSES), weight=1)
            for i, status in enumerate(STATUSES):
                frame = customtkinter.CTkFrame(self)
                frame.grid(row=1, column=i, padx=20, pady=10, sticky="nsew")
                label = customtkinter.CTkLabel(frame, text=status.capitalize(), font=customtkinter.CTkFont(size=18, weight="bold"))
                label.pack(padx=10, pady=10)
                scrollable_frame = customtkinter.CTkScrollableFrame(frame, label_text="")
                scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)
                self.status_frames[status] = frame
                self.status_scrollable_frames[status] = scrollable_frame

        tasks_by_status = {status: [] for status in STATUSES}
        for task in self.tasks:
            # Vérifie que le statut est valide, sinon attribue 'Todo' comme statut par défaut
            if task['status'] not in tasks_by_status:
                task['status'] = 'Todo'  # Définit 'Todo' comme statut par défaut si ce n'est pas valide
            tasks_by_status[task['status']].append(task)

        # Affiche les tâches dans leurs colonnes respectives
        for status, tasks in tasks_by_status.items():
            if status in self.status_scrollable_frames:
                for task in tasks:
                    task_frame = TaskFrame(self.status_scrollable_frames[status], task, self)
                    task_frame.pack(padx=10, pady=5, fill="x")


if __name__ == "__main__":
    current_file = os.path.abspath(__file__)
    check_for_updates(current_file)

    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    app = KanbanBoardApp()
    app.mainloop()
