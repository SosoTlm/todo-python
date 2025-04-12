import customtkinter
import tkinter.messagebox
import json
import os
import uuid
from datetime import datetime

# --- Constants ---
DATA_FILE = "kanban_tasks.json"
STATUSES = ["todo", "inprogress", "done"]
PRIORITIES = ["low", "medium", "high"]

# --- Task Structure (using dictionary) ---
def create_task(title, description, status="todo", priority="medium", due_date=None):
    if status not in STATUSES:
        print(f"Warning: Invalid status '{status}'. Defaulting to 'todo'.")
        status = "todo"
    if priority not in PRIORITIES:
        print(f"Warning: Invalid priority '{priority}'. Defaulting to 'medium'.")
        priority = "medium"
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

    def _get_priority_color(self, priority):
        if priority == 'high':
            return "red"
        elif priority == 'medium':
            return "yellow"
        else:
            return "green"

    def show_details(self, event):
        EditTaskDialog(self.app, self.task)

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

class KanbanBoardApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("CustomTkinter Kanban Board")
        self.geometry("1000x600")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.tasks = load_tasks()

        self.add_task_button = customtkinter.CTkButton(self, text="Add New Task", command=self.show_add_task_dialog)
        self.add_task_button.grid(row=0, column=0, columnspan=3, padx=20, pady=10, sticky="ew")

        self.todo_frame = customtkinter.CTkFrame(self)
        self.todo_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.todo_label = customtkinter.CTkLabel(self.todo_frame, text="To Do", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.todo_label.pack(padx=10, pady=10)
        self.todo_scrollable_frame = customtkinter.CTkScrollableFrame(self.todo_frame, label_text="")
        self.todo_scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.inprogress_frame = customtkinter.CTkFrame(self)
        self.inprogress_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        self.inprogress_label = customtkinter.CTkLabel(self.inprogress_frame, text="In Progress", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.inprogress_label.pack(padx=10, pady=10)
        self.inprogress_scrollable_frame = customtkinter.CTkScrollableFrame(self.inprogress_frame, label_text="")
        self.inprogress_scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.done_frame = customtkinter.CTkFrame(self)
        self.done_frame.grid(row=1, column=2, padx=20, pady=10, sticky="nsew")
        self.done_label = customtkinter.CTkLabel(self.done_frame, text="Done", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.done_label.pack(padx=10, pady=10)
        self.done_scrollable_frame = customtkinter.CTkScrollableFrame(self.done_frame, label_text="")
        self.done_scrollable_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.update_board()

    def show_add_task_dialog(self):
        AddTaskDialog(self)

    def update_board(self):
        for frame in [self.todo_scrollable_frame, self.inprogress_scrollable_frame, self.done_scrollable_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        tasks_by_status = {status: [] for status in STATUSES}
        for task in self.tasks:
            tasks_by_status[task['status']].append(task)

        for task in tasks_by_status['todo']:
            task_frame = TaskFrame(self.todo_scrollable_frame, task, self)
            task_frame.pack(padx=10, pady=5, fill="x")
        for task in tasks_by_status['inprogress']:
            task_frame = TaskFrame(self.inprogress_scrollable_frame, task, self)
            task_frame.pack(padx=10, pady=5, fill="x")
        for task in tasks_by_status['done']:
            task_frame = TaskFrame(self.done_scrollable_frame, task, self)
            task_frame.pack(padx=10, pady=5, fill="x")

if __name__ == "__main__":
    customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    app = KanbanBoardApp()
    app.mainloop()
