import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.auth import auth
from core.utils import generate_invitation_code
from database import SessionLocal, Course, Task, Enrollment, Submission, User
from datetime import datetime, timezone

class TeacherDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"Teacher Dashboard - Welcome, {auth.current_user.first_name}!", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self.logout, style='Danger.TButton').pack(side=tk.RIGHT)
        
        # Body
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        # Actions
        actions = ttk.Frame(body)
        actions.pack(fill=tk.X, pady=(0, 20))
        ttk.Button(actions, text="+ Create New Course", style='Success.TButton', command=self.create_course).pack(side=tk.LEFT)
        
        ttk.Label(body, text="Your Courses", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Course List
        self.course_frame = ttk.Frame(body)
        self.course_frame.pack(fill=tk.BOTH, expand=True)
        self.load_courses()
        
    def load_courses(self):
        for widget in self.course_frame.winfo_children():
            widget.destroy()
            
        db = SessionLocal()
        try:
            courses = db.query(Course).filter(Course.teacher_id == auth.current_user.id).all()
            if not courses:
                ttk.Label(self.course_frame, text="You haven't created any courses yet.").pack(anchor=tk.W)
            else:
                for c in courses:
                    card = ttk.Frame(self.course_frame, style='Card.TFrame', padding=10)
                    card.pack(fill=tk.X, pady=5)
                    
                    ttk.Label(card, text=c.title, font=('', 14, 'bold'), style='Card.TLabel').pack(side=tk.LEFT)
                    ttk.Label(card, text=f"Code: {c.invitation_code}", style='Card.TLabel').pack(side=tk.LEFT, padx=20)
                    
                    ttk.Button(card, text="Manage", command=lambda cid=c.id: self.manage_course(cid)).pack(side=tk.RIGHT)
        finally:
            db.close()

    def create_course(self):
        title = simpledialog.askstring("Create Course", "Enter Course Title:")
        if not title:
            return
            
        description = simpledialog.askstring("Create Course", "Enter Course Description:")
        if not description:
            description = ""
            
        db = SessionLocal()
        try:
            course = Course(
                title=title,
                description=description,
                invitation_code=generate_invitation_code(),
                teacher_id=auth.current_user.id
            )
            db.add(course)
            db.commit()
            messagebox.showinfo("Success", f"Course created! Invitation code: {course.invitation_code}")
            self.load_courses()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            db.close()

    def manage_course(self, course_id):
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        screen = TeacherCourseView(self.controller.container, self.controller, course_id)
        screen.pack(fill=tk.BOTH, expand=True)

    def logout(self):
        auth.logout()
        self.controller.show_login()

class TeacherCourseView(ttk.Frame):
    def __init__(self, parent, controller, course_id):
        super().__init__(parent)
        self.controller = controller
        self.course_id = course_id
        
        db = SessionLocal()
        self.course = db.query(Course).get(course_id)
        db.close()
        
        # Header
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        ttk.Button(header, text="← Back to Dashboard", command=self.controller.show_dashboard).pack(side=tk.LEFT)
        ttk.Label(header, text=f"Manage: {self.course.title}", style='Title.TLabel').pack(side=tk.LEFT, padx=20)
        ttk.Label(header, text=f"Code: {self.course.invitation_code}", font=('', 14)).pack(side=tk.RIGHT)
        
        # Body layout (Notebook for tabs)
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        notebook = ttk.Notebook(body)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Tasks
        self.tasks_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.tasks_tab, text="Tasks")
        
        # Tab 2: Students
        self.students_tab = ttk.Frame(notebook, padding=10)
        notebook.add(self.students_tab, text="Students")
        
        self.build_tasks_tab()
        self.build_students_tab()
        
    def build_tasks_tab(self):
        actions = ttk.Frame(self.tasks_tab)
        actions.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions, text="+ Create Task", style='Success.TButton', command=self.create_task).pack(side=tk.LEFT)
        
        self.tasks_list = ttk.Frame(self.tasks_tab)
        self.tasks_list.pack(fill=tk.BOTH, expand=True)
        self.load_tasks()
        
    def load_tasks(self):
        for widget in self.tasks_list.winfo_children():
            widget.destroy()
            
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.course_id == self.course_id).all()
            if not tasks:
                ttk.Label(self.tasks_list, text="No tasks created yet.").pack(anchor=tk.W)
            else:
                for t in tasks:
                    card = ttk.Frame(self.tasks_list, style='Card.TFrame', padding=10)
                    card.pack(fill=tk.X, pady=5)
                    
                    ttk.Label(card, text=t.title, font=('', 12, 'bold'), style='Card.TLabel').pack(side=tk.LEFT)
                    
                    subs_count = db.query(Submission).filter(Submission.task_id == t.id).count()
                    ttk.Label(card, text=f"Submissions: {subs_count}", style='Card.TLabel').pack(side=tk.LEFT, padx=30)
                    
                    ttk.Button(card, text="View Submissions", command=lambda tid=t.id: self.view_task(tid)).pack(side=tk.RIGHT)
        finally:
            db.close()

    def create_task(self):
        # Custom popup
        top = tk.Toplevel(self)
        top.title("Create Task")
        top.geometry("400x300")
        
        ttk.Label(top, text="Task Title:").pack(anchor=tk.W, padx=10, pady=5)
        title_entry = ttk.Entry(top, width=40)
        title_entry.pack(padx=10, pady=5)
        
        ttk.Label(top, text="Task Description (Instructions):").pack(anchor=tk.W, padx=10, pady=5)
        desc_text = tk.Text(top, height=8, width=40, bg="white", fg="black")
        desc_text.pack(padx=10, pady=5)
        
        def save():
            title = title_entry.get().strip()
            desc = desc_text.get("1.0", tk.END).strip()
            if not title or not desc:
                messagebox.showerror("Error", "Please fill all fields", parent=top)
                return
                
            db = SessionLocal()
            try:
                task = Task(title=title, description=desc, course_id=self.course_id)
                db.add(task)
                db.commit()
                top.destroy()
                self.load_tasks()
            finally:
                db.close()
                
        ttk.Button(top, text="Save Task", style='Primary.TButton', command=save).pack(pady=10)

    def view_task(self, task_id):
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        screen = TaskSubmissionsView(self.controller.container, self.controller, self.course_id, task_id)
        screen.pack(fill=tk.BOTH, expand=True)

    def build_students_tab(self):
        db = SessionLocal()
        try:
            enrollments = db.query(Enrollment).filter(Enrollment.course_id == self.course_id).all()
            if not enrollments:
                ttk.Label(self.students_tab, text="No students enrolled yet.").pack(anchor=tk.W)
            else:
                for idx, e in enumerate(enrollments):
                    ttk.Label(self.students_tab, text=f"{idx+1}. {e.student.full_name} ({e.student.email})").pack(anchor=tk.W, pady=2)
        finally:
            db.close()

class TaskSubmissionsView(ttk.Frame):
    def __init__(self, parent, controller, course_id, task_id):
        super().__init__(parent)
        self.controller = controller
        self.course_id = course_id
        self.task_id = task_id
        
        db = SessionLocal()
        self.task = db.query(Task).get(task_id)
        db.close()
        
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        btn = ttk.Button(header, text="← Back to Course", 
                         command=lambda: self.return_to_course())
        btn.pack(side=tk.LEFT)
        ttk.Label(header, text=f"Submissions for: {self.task.title}", style='Title.TLabel').pack(side=tk.LEFT, padx=20)
        
        # Submissions Treeview
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        columns = ('student', 'status', 'ai_score', 'date')
        self.tree = ttk.Treeview(body, columns=columns, show='headings')
        self.tree.heading('student', text='Student')
        self.tree.heading('status', text='Status')
        self.tree.heading('ai_score', text='AI Score')
        self.tree.heading('date', text='Submission Date')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind('<Double-1>', self.on_double_click)
        
        self.load_submissions()
        
    def load_submissions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        db = SessionLocal()
        try:
            subs = db.query(Submission).filter(Submission.task_id == self.task_id).all()
            for s in subs:
                score = f"{s.ai_score}/7" if s.status == 'completed' else "N/A"
                date_str = s.submitted_at.strftime("%Y-%m-%d %H:%M") if s.submitted_at else "Unknown"
                self.tree.insert('', tk.END, values=(s.student.full_name, s.status, score, date_str), iid=str(s.id))
        finally:
            db.close()
            
    def return_to_course(self):
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        from ui.teacher_ui import TeacherCourseView
        screen = TeacherCourseView(self.controller.container, self.controller, self.course_id)
        screen.pack(fill=tk.BOTH, expand=True)
        
    def on_double_click(self, event):
        item = self.tree.selection()[0]
        sub_id = int(item)
        
        top = tk.Toplevel(self)
        top.title("Review Submission")
        top.geometry("800x600")
        
        db = SessionLocal()
        sub = db.query(Submission).get(sub_id)
        db.close()
        
        ttk.Label(top, text=f"Student: {sub.student.full_name}", font=('', 14, 'bold')).pack(pady=10)
        
        content = tk.Text(top, height=10, width=80, bg="white", fg="black")
        content.insert(tk.END, sub.content if sub.content else f"File uploaded: {sub.file_name}")
        content.config(state=tk.DISABLED)
        content.pack(pady=10)
        
        ttk.Label(top, text=f"AI Score: {sub.ai_score}/7", font=('', 12, 'bold')).pack()
        
        feedback = tk.Text(top, height=15, width=80, bg="white", fg="black")
        feedback.insert(tk.END, sub.ai_feedback if sub.ai_feedback else "No feedback available.")
        feedback.config(state=tk.DISABLED)
        feedback.pack(pady=10)
