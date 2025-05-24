import customtkinter as ctk
import tkinter as tk
import json
import os
import uuid
from datetime import datetime
import threading
import time
import urllib
import urllib.request

UPDATE_URL = "https://raw.githubusercontent.com/SosoTlm/todo-python/refs/heads/main/Todo%20Python.py"

# Fonction pour calculer le hash SHA256 du fichier donné
def file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

# Fonction principale de mise à jour
def check_for_update():
    local_file = os.path.realpath(__file__)
    try:
        with urllib.request.urlopen(UPDATE_URL) as response:
            latest_code = response.read()
            latest_hash = hashlib.sha256(latest_code).hexdigest()

        current_hash = file_hash(local_file)
        
        if latest_hash != current_hash:
            print("🔁 Mise à jour disponible ! Mise à jour en cours...")
            with open(local_file, "wb") as f:
                f.write(latest_code)
            print("✅ Mise à jour terminée. Redémarrage...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            print("🟢 Aucune mise à jour nécessaire.")
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification des mises à jour : {e}")

check_for_update()

# Constants
DATA_FILE = "tasks.json"
STATUSES = ["Todo", "InProgress", "Done"]
PRIORITIES = ["Low", "Important", "Urgent"]

class ModernTodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.tasks = self.load_tasks()
        self.setup_ui()
        self.show_loading()
        
    def setup_window(self):
        self.title("Ultra Modern Todo")
        # Adaptive window sizing
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        if screen_width >= 1920:
            width, height = 1400, 900
        elif screen_width >= 1366:
            width, height = 1200, 800
        else:
            width, height = min(1000, screen_width-100), min(700, screen_height-100)
            
        self.geometry(f"{width}x{height}")
        self.minsize(800, 600)
        
        # Center window
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # Modern theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
    def setup_ui(self):
        # Main container with padding that adapts to window size
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Animated header
        self.header_frame = ctk.CTkFrame(self.main_frame, height=100, fg_color=("gray90", "gray13"))
        self.header_frame.pack(fill="x", pady=(0, 20))
        self.header_frame.pack_propagate(False)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="✨ Todo Python", 
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#1e40af", "#3b82f6")
        )
        self.title_label.pack(expand=True)
        
        # Controls with modern styling
        self.controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.controls_frame.pack(fill="x", pady=(0, 20))
        
        self.add_btn = ctk.CTkButton(
            self.controls_frame,
            text="➕ Add Task",
            command=self.show_add_dialog,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=20,
            hover_color=("#2563eb", "#1d4ed8")
        )
        self.add_btn.pack(side="left", padx=(0, 10))
        
        self.settings_btn = ctk.CTkButton(
            self.controls_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=20,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35")
        )
        self.settings_btn.pack(side="left")
        
        # Task board with responsive columns
        self.board_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.board_frame.pack(fill="both", expand=True)
        
        # Configure responsive grid
        for i in range(len(STATUSES)):
            self.board_frame.grid_columnconfigure(i, weight=1, uniform="col")
        self.board_frame.grid_rowconfigure(0, weight=1)
        
        self.columns = {}
        self.create_columns()
        self.update_board()
        
    def create_columns(self):
        colors = [("#ef4444", "#dc2626"), ("#f59e0b", "#d97706"), ("#10b981", "#059669")]
        
        for i, status in enumerate(STATUSES):
            # Column container
            col = ctk.CTkFrame(self.board_frame, corner_radius=15)
            col.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            
            # Header with status indicator
            header = ctk.CTkFrame(col, height=60, fg_color=colors[i], corner_radius=10)
            header.pack(fill="x", padx=10, pady=(10, 5))
            header.pack_propagate(False)
            
            title = ctk.CTkLabel(
                header, 
                text=f"{status} ({len([t for t in self.tasks if t['status'] == status])})",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="white"
            )
            title.pack(expand=True)
            
            # Scrollable task area
            scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=10, pady=(5, 10))
            
            self.columns[status] = {"frame": col, "header": header, "title": title, "scroll": scroll}
    
    def update_board(self):
        # Clear existing tasks
        for status_data in self.columns.values():
            for widget in status_data["scroll"].winfo_children():
                widget.destroy()
        
        # Group tasks by status
        tasks_by_status = {status: [] for status in STATUSES}
        for task in self.tasks:
            if task["status"] in tasks_by_status:
                tasks_by_status[task["status"]].append(task)
        
        # Create task cards with animations
        for status, tasks in tasks_by_status.items():
            # Update header count
            self.columns[status]["title"].configure(
                text=f"{status} ({len(tasks)})"
            )
            
            for task in tasks:
                self.create_task_card(self.columns[status]["scroll"], task)
    
    def create_task_card(self, parent, task):
        # Priority colors
        priority_colors = {
            "Low": ("#10b981", "#059669"),
            "Important": ("#f59e0b", "#d97706"),
            "Urgent": ("#ef4444", "#dc2626")
        }
        
        # Card container with hover effects
        card = ctk.CTkFrame(
            parent, 
            corner_radius=10,
            fg_color=("gray92", "gray14"),
            border_width=1,
            border_color=("gray80", "gray25")
        )
        card.pack(fill="x", pady=5)
        
        # Task title
        title = ctk.CTkLabel(
            card,
            text=task["title"],
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title.pack(fill="x", padx=15, pady=(15, 5))
        
        # Priority indicator
        priority_frame = ctk.CTkFrame(card, fg_color="transparent")
        priority_frame.pack(fill="x", padx=15)
        
        priority_badge = ctk.CTkLabel(
            priority_frame,
            text=f"🔥 {task['priority']}",
            font=ctk.CTkFont(size=12),
            fg_color=priority_colors[task["priority"]],
            corner_radius=15,
            width=80,
            height=25
        )
        priority_badge.pack(side="left")
        
        # Description preview
        if task["description"]:
            desc = ctk.CTkLabel(
                card,
                text=task["description"][:50] + ("..." if len(task["description"]) > 50 else ""),
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray60"),
                anchor="w"
            )
            desc.pack(fill="x", padx=15, pady=5)
        
        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            width=30,
            height=25,
            corner_radius=5,
            command=lambda: self.edit_task(task),
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40")
        )
        edit_btn.pack(side="left", padx=(0, 5))
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️",
            width=30,
            height=25,
            corner_radius=5,
            command=lambda: self.delete_task(task),
            fg_color=("#ef4444", "#dc2626"),
            hover_color=("#dc2626", "#b91c1c")
        )
        delete_btn.pack(side="left")
        
        # Move buttons (with smooth transitions)
        if task["status"] != STATUSES[-1]:
            move_btn = ctk.CTkButton(
                btn_frame,
                text="➡️",
                width=30,
                height=25,
                corner_radius=5,
                command=lambda: self.move_task(task, 1),
                fg_color=("#10b981", "#059669")
            )
            move_btn.pack(side="right")
        
        if task["status"] != STATUSES[0]:
            back_btn = ctk.CTkButton(
                btn_frame,
                text="⬅️",
                width=30,
                height=25,
                corner_radius=5,
                command=lambda: self.move_task(task, -1),
                fg_color=("#6b7280", "#4b5563")
            )
            back_btn.pack(side="right", padx=(5, 0))
    
    def show_loading(self):
        # Loading overlay
        self.loading_frame = ctk.CTkFrame(
            self,
            fg_color=("gray95", "gray10"),
            corner_radius=0
        )
        self.loading_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Loading animation
        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="⚡ Loading Todo Python...",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1e40af", "#3b82f6")
        )
        self.loading_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self.loading_frame, width=300)
        self.progress.place(relx=0.5, rely=0.6, anchor="center")
        self.progress.set(0)
        
        # Animate loading
        threading.Thread(target=self.animate_loading, daemon=True).start()
    
    def animate_loading(self):
        for i in range(101):
            self.progress.set(i / 100)
            time.sleep(0.02)
        
        self.after(500, self.hide_loading)
    
    def hide_loading(self):
        self.loading_frame.destroy()
    
    def show_add_dialog(self):
        AddTaskDialog(self)
    
    def show_settings(self):
        SettingsDialog(self)
    
    def edit_task(self, task):
        EditTaskDialog(self, task)
    
    def delete_task(self, task):
        if tk.messagebox.askyesno("Delete Task", f"Delete '{task['title']}'?"):
            self.tasks.remove(task)
            self.save_tasks()
            self.update_board()
    
    def move_task(self, task, direction):
        current_idx = STATUSES.index(task["status"])
        new_idx = current_idx + direction
        
        if 0 <= new_idx < len(STATUSES):
            task["status"] = STATUSES[new_idx]
            task["updated_at"] = datetime.now().isoformat()
            self.save_tasks()
            self.update_board()
    
    def load_tasks(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_tasks(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)

class AddTaskDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("➕ Add New Task")
        self.geometry("450x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.after(10, self.center_dialog)
        
        self.setup_ui()
    
    def center_dialog(self):
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - 450) // 2
        y = parent_y + (parent_height - 400) // 2
        self.geometry(f"450x400+{x}+{y}")
    
    def setup_ui(self):
        # Main container
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title field
        ctk.CTkLabel(main, text="Task Title", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.title_entry = ctk.CTkEntry(main, height=40, corner_radius=10)
        self.title_entry.pack(fill="x", pady=(0, 15))
        
        # Description field
        ctk.CTkLabel(main, text="Description", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.desc_text = ctk.CTkTextbox(main, height=80, corner_radius=10)
        self.desc_text.pack(fill="x", pady=(0, 15))
        
        # Priority and Status in one row
        row_frame = ctk.CTkFrame(main, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 15))
        
        # Priority
        left_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(left_frame, text="Priority", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.priority_var = ctk.StringVar(value="Important")
        self.priority_menu = ctk.CTkOptionMenu(left_frame, values=PRIORITIES, variable=self.priority_var, height=35)
        self.priority_menu.pack(fill="x")
        
        # Status
        right_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(right_frame, text="Status", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.status_var = ctk.StringVar(value="Todo")
        self.status_menu = ctk.CTkOptionMenu(right_frame, values=STATUSES, variable=self.status_var, height=35)
        self.status_menu.pack(fill="x")
        
        # Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=("gray75", "gray25"),
            hover_color=("gray65", "gray35"),
            height=40,
            corner_radius=10
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="✨ Create Task",
            command=self.create_task,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="right")
        
        self.title_entry.focus()
    
    def create_task(self):
        title = self.title_entry.get().strip()
        if not title:
            tk.messagebox.showerror("Error", "Title is required!")
            return
        
        task = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": self.desc_text.get("0.0", "end").strip(),
            "priority": self.priority_var.get(),
            "status": self.status_var.get(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.parent.tasks.append(task)
        self.parent.save_tasks()
        self.parent.update_board()
        self.destroy()

class EditTaskDialog(AddTaskDialog):
    def __init__(self, parent, task):
        self.task = task
        super().__init__(parent)
        self.title(f"✏️ Edit: {task['title']}")
        self.populate_fields()
    
    def populate_fields(self):
        self.title_entry.insert(0, self.task["title"])
        self.desc_text.insert("0.0", self.task["description"])
        self.priority_var.set(self.task["priority"])
        self.status_var.set(self.task["status"])
    
    def create_task(self):
        title = self.title_entry.get().strip()
        if not title:
            tk.messagebox.showerror("Error", "Title is required!")
            return
        
        self.task.update({
            "title": title,
            "description": self.desc_text.get("0.0", "end").strip(),
            "priority": self.priority_var.get(),
            "status": self.status_var.get(),
            "updated_at": datetime.now().isoformat()
        })
        
        self.parent.save_tasks()
        self.parent.update_board()
        self.destroy()

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("⚙️ Settings")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self.after(10, self.center_dialog)
        self.setup_ui()
    
    def center_dialog(self):
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 300) // 2
        self.geometry(f"400x300+{x}+{y}")
    
    def setup_ui(self):
        main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Theme selection
        ctk.CTkLabel(main, text="🎨 Appearance", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(0, 15))
        
        theme_frame = ctk.CTkFrame(main)
        theme_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(theme_frame, text="Theme Mode:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            variable=self.theme_var,
            command=self.change_theme
        )
        theme_menu.pack(fill="x", padx=15, pady=(0, 15))
        
        # About section
        ctk.CTkLabel(main, text="ℹ️ About", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(20, 15))
        
        about_frame = ctk.CTkFrame(main)
        about_frame.pack(fill="x")
        
        ctk.CTkLabel(
            about_frame,
            text="Todo Python\nBuilt with CustomTkinter\n\n✨ Features:\n• Responsive design\n• Smooth animations\n• Modern UI/UX",
            justify="left",
            font=ctk.CTkFont(size=12)
        ).pack(padx=15, pady=15)
    
    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)

if __name__ == "__main__":
    app = ModernTodoApp()
    app.mainloop()
