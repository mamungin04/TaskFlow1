"""
TaskFlow - Academic Task Management Application
CSCI 401 Senior Design Project
Python standard-library prototype aligned with the TaskFlow Testing Specification.

Run: python taskflow.py
Data is stored locally in taskflow.db in the same folder.
"""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

DB_FILE = "taskflow.db"
DATE_FORMAT = "%Y-%m-%d"


def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            course_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('Low','Medium','High')),
            status TEXT NOT NULL DEFAULT 'Active'
                CHECK(status IN ('Active','Completed')),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)
    conn.commit()
    return conn


class TaskFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskFlow | Academic Task Manager")
        self.root.geometry("1050x680")
        self.root.minsize(900, 580)
        self.conn = connect_db()
        self.selected_task_id = None

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("Title.TLabel", font=("Arial", 20, "bold"))
        self.style.configure("Sub.TLabel", font=("Arial", 10))
        self.style.configure("Treeview", rowheight=28, font=("Arial", 10))
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.build_ui()
        self.refresh_courses()
        self.refresh_tasks()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(18, 14))
        header.pack(fill="x")
        ttk.Label(header, text="TaskFlow", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Keep assignments, exams, projects, and deadlines organized in one place.",
            style="Sub.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        main = ttk.Frame(self.root, padding=(18, 0, 18, 14))
        main.pack(fill="both", expand=True)

        course_frame = ttk.LabelFrame(main, text="Courses", padding=10)
        course_frame.pack(fill="x", pady=(0, 10))
        self.course_entry = ttk.Entry(course_frame, width=34)
        self.course_entry.pack(side="left", padx=(0, 8))
        self.course_entry.insert(0, "")
        ttk.Button(course_frame, text="Add Course", command=self.add_course).pack(side="left")
        ttk.Label(course_frame, text="Add your courses before assigning tasks.").pack(side="left", padx=12)

        form = ttk.LabelFrame(main, text="Task Details", padding=10)
        form.pack(fill="x", pady=(0, 10))
        for col in (1, 3):
            form.columnconfigure(col, weight=1)

        ttk.Label(form, text="Title *").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.title_entry = ttk.Entry(form)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=4)
        ttk.Label(form, text="Course *").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=4)
        self.course_combo = ttk.Combobox(form, state="readonly")
        self.course_combo.grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="Due date * (YYYY-MM-DD)").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        self.date_entry = ttk.Entry(form)
        self.date_entry.grid(row=1, column=1, sticky="ew", padx=(0, 14), pady=4)
        self.date_entry.insert(0, date.today().strftime(DATE_FORMAT))
        ttk.Label(form, text="Priority *").grid(row=1, column=2, sticky="w", padx=(0, 6), pady=4)
        self.priority_combo = ttk.Combobox(form, values=("Low", "Medium", "High"), state="readonly")
        self.priority_combo.set("Medium")
        self.priority_combo.grid(row=1, column=3, sticky="ew", pady=4)

        ttk.Label(form, text="Description").grid(row=2, column=0, sticky="nw", padx=(0, 6), pady=4)
        self.description_text = tk.Text(form, height=2, width=40, wrap="word")
        self.description_text.grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)

        actions = ttk.Frame(form)
        actions.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Button(actions, text="Save New Task", command=self.create_task).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Update Selected", command=self.update_task).pack(side="left", padx=6)
        ttk.Button(actions, text="Mark Completed", command=self.complete_task).pack(side="left", padx=6)
        ttk.Button(actions, text="Delete Selected", command=self.delete_task).pack(side="left", padx=6)
        ttk.Button(actions, text="Clear Form", command=self.clear_form).pack(side="left", padx=6)

        filters = ttk.LabelFrame(main, text="Dashboard Filters", padding=8)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text="Course").pack(side="left")
        self.filter_course = ttk.Combobox(filters, width=19, state="readonly")
        self.filter_course.pack(side="left", padx=(5, 14))
        self.filter_course.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())
        ttk.Label(filters, text="Priority").pack(side="left")
        self.filter_priority = ttk.Combobox(filters, width=12, values=("All", "Low", "Medium", "High"), state="readonly")
        self.filter_priority.set("All")
        self.filter_priority.pack(side="left", padx=(5, 14))
        self.filter_priority.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())
        ttk.Label(filters, text="Status").pack(side="left")
        self.filter_status = ttk.Combobox(filters, width=13, values=("All", "Active", "Completed"), state="readonly")
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=(5, 14))
        self.filter_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tasks())
        ttk.Button(filters, text="Sort by Due Date", command=self.sort_by_due_date).pack(side="left", padx=4)
        ttk.Button(filters, text="Show All", command=self.reset_filters).pack(side="left", padx=4)

        table_frame = ttk.Frame(main)
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "title", "course", "due", "priority", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {"id": "ID", "title": "Task", "course": "Course", "due": "Due Date",
                    "priority": "Priority", "status": "Status"}
        widths = {"id": 45, "title": 260, "course": 190, "due": 115, "priority": 90, "status": 100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.status_label = ttk.Label(main, text="Ready", anchor="w")
        self.status_label.pack(fill="x", pady=(6, 0))

    def add_course(self):
        name = self.course_entry.get().strip()
        if not name:
            messagebox.showerror("Course Required", "Enter a course name.")
            return
        try:
            self.conn.execute("INSERT INTO courses(name) VALUES (?)", (name,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Course Exists", "That course already exists.")
            return
        self.course_entry.delete(0, "end")
        self.refresh_courses()
        self.status_label.config(text=f"Course added: {name}")

    def refresh_courses(self):
        rows = self.conn.execute("SELECT id, name FROM courses ORDER BY name").fetchall()
        self.course_map = {name: course_id for course_id, name in rows}
        names = list(self.course_map.keys())
        self.course_combo["values"] = names
        current = self.course_combo.get()
        if current not in names:
            self.course_combo.set(names[0] if names else "")
        self.filter_course["values"] = ["All"] + names
        if self.filter_course.get() not in self.filter_course["values"]:
            self.filter_course.set("All")

    def validate_form(self):
        title = self.title_entry.get().strip()
        course = self.course_combo.get().strip()
        due = self.date_entry.get().strip()
        priority = self.priority_combo.get().strip()
        description = self.description_text.get("1.0", "end").strip()
        if not title:
            messagebox.showerror("Invalid Task", "Please enter a task title.")
            return None
        if not course or course not in self.course_map:
            messagebox.showerror("Invalid Task", "Please add and select a course.")
            return None
        try:
            datetime.strptime(due, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Invalid Date", "Enter a valid date in YYYY-MM-DD format, for example 2026-11-15.")
            return None
        if priority not in ("Low", "Medium", "High"):
            messagebox.showerror("Invalid Priority", "Choose Low, Medium, or High.")
            return None
        return title, description, self.course_map[course], due, priority

    def create_task(self):
        values = self.validate_form()
        if values is None:
            return
        self.conn.execute(
            "INSERT INTO tasks(title, description, course_id, due_date, priority, status) VALUES (?,?,?,?,?,'Active')",
            values
        )
        self.conn.commit()
        self.refresh_tasks()
        self.clear_form()
        self.status_label.config(text="Task created and saved.")

    def update_task(self):
        if self.selected_task_id is None:
            messagebox.showinfo("Select a Task", "Select a task from the Dashboard first.")
            return
        values = self.validate_form()
        if values is None:
            return
        self.conn.execute(
            "UPDATE tasks SET title=?, description=?, course_id=?, due_date=?, priority=? WHERE id=?",
            (*values, self.selected_task_id)
        )
        self.conn.commit()
        task_id = self.selected_task_id
        self.refresh_tasks()
        self.select_row(task_id)
        self.status_label.config(text="Task updated and saved.")

    def complete_task(self):
        task_id = self.get_selected_id()
        if task_id is None:
            messagebox.showinfo("Select a Task", "Select a task from the Dashboard first.")
            return
        self.conn.execute("UPDATE tasks SET status='Completed' WHERE id=?", (task_id,))
        self.conn.commit()
        self.refresh_tasks()
        self.status_label.config(text="Task marked as Completed.")

    def delete_task(self):
        task_id = self.get_selected_id()
        if task_id is None:
            messagebox.showinfo("Select a Task", "Select a task from the Dashboard first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete the selected task?"):
            return
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()
        self.refresh_tasks()
        self.clear_form()
        self.status_label.config(text="Task deleted.")

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return int(self.tree.item(selection[0], "values")[0])

    def on_select(self, _event=None):
        task_id = self.get_selected_id()
        if task_id is None:
            return
        row = self.conn.execute("""
            SELECT t.title, t.description, c.name, t.due_date, t.priority
            FROM tasks t JOIN courses c ON c.id=t.course_id WHERE t.id=?
        """, (task_id,)).fetchone()
        if row:
            self.selected_task_id = task_id
            title, description, course, due, priority = row
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, title)
            self.description_text.delete("1.0", "end")
            self.description_text.insert("1.0", description)
            self.course_combo.set(course)
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, due)
            self.priority_combo.set(priority)

    def select_row(self, task_id):
        for item in self.tree.get_children():
            if int(self.tree.item(item, "values")[0]) == task_id:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.tree.see(item)
                break

    def refresh_tasks(self, order_by="t.id DESC"):
        if not hasattr(self, "tree"):
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        where = []
        params = []
        course = self.filter_course.get() if hasattr(self, "filter_course") else "All"
        priority = self.filter_priority.get() if hasattr(self, "filter_priority") else "All"
        status = self.filter_status.get() if hasattr(self, "filter_status") else "All"
        if course and course != "All":
            where.append("c.name=?")
            params.append(course)
        if priority and priority != "All":
            where.append("t.priority=?")
            params.append(priority)
        if status and status != "All":
            where.append("t.status=?")
            params.append(status)
        sql = """
            SELECT t.id, t.title, c.name, t.due_date, t.priority, t.status
            FROM tasks t JOIN courses c ON c.id=t.course_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY " + order_by
        rows = self.conn.execute(sql, params).fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)
        self.status_label.config(text=f"Dashboard: {len(rows)} task(s) shown.")

    def sort_by_due_date(self):
        self.refresh_tasks("t.due_date ASC, t.id DESC")

    def reset_filters(self):
        self.filter_course.set("All")
        self.filter_priority.set("All")
        self.filter_status.set("All")
        self.refresh_tasks()

    def clear_form(self):
        self.selected_task_id = None
        self.title_entry.delete(0, "end")
        self.description_text.delete("1.0", "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, date.today().strftime(DATE_FORMAT))
        self.priority_combo.set("Medium")
        if self.course_combo["values"]:
            self.course_combo.set(self.course_combo["values"][0])
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def close_app(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskFlowApp(root)
    root.mainloop()
