import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from core.auth import auth
from database import SessionLocal, Course, Enrollment, Task, Submission
from core.ai_evaluator import evaluate_submission_with_ai

class StudentDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        ttk.Label(header, text=f"Welcome, {auth.current_user.first_name}!", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header, text="Logout", command=self.logout, style='Danger.TButton').pack(side=tk.RIGHT)
        
        # Body
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (Courses)
        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left, text="My Courses", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Course List
        self.course_frame = ttk.Frame(left)
        self.course_frame.pack(fill=tk.BOTH, expand=True)
        self.load_courses()
        
        # Right Panel (Join Course)
        right = ttk.Frame(body, padding=20)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        
        card = ttk.Frame(right, style='Card.TFrame', padding=20)
        card.pack()
        
        ttk.Label(card, text="Join a Course", style='Card.TLabel', font=('', 14, 'bold')).pack(pady=(0, 10))
        self.code_entry = ttk.Entry(card, width=20)
        self.code_entry.pack(pady=5)
        ttk.Button(card, text="Join", style='Success.TButton', command=self.join_course).pack(fill=tk.X, pady=5)
        
    def load_courses(self):
        for widget in self.course_frame.winfo_children():
            widget.destroy()
            
        db = SessionLocal()
        try:
            enrollments = db.query(Enrollment).filter(Enrollment.student_id == auth.current_user.id).all()
            if not enrollments:
                ttk.Label(self.course_frame, text="You haven't joined any courses yet.").pack(anchor=tk.W)
            else:
                for e in enrollments:
                    course = e.course
                    row = ttk.Frame(self.course_frame)
                    row.pack(fill=tk.X, pady=2)
                    btn = ttk.Button(
                        row, 
                        text=f"{course.title} (Teacher: {course.teacher.full_name})",
                        command=lambda c_id=course.id: self.view_course(c_id)
                    )
                    btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    leave_btn = ttk.Button(
                        row,
                        text="Leave",
                        style='Danger.TButton',
                        command=lambda c_id=course.id, c_title=course.title: self.leave_course(c_id, c_title)
                    )
                    leave_btn.pack(side=tk.RIGHT, padx=(5, 0))
        finally:
            db.close()

    def join_course(self):
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showwarning("Error", "Please enter an invitation code")
            return
            
        db = SessionLocal()
        try:
            course = db.query(Course).filter(Course.invitation_code == code).first()
            if not course:
                messagebox.showerror("Error", "Course not found")
                return
                
            existing = db.query(Enrollment).filter(
                Enrollment.student_id == auth.current_user.id,
                Enrollment.course_id == course.id
            ).first()
            if existing:
                messagebox.showinfo("Info", "You are already enrolled in this course")
                return
                
            enrollment = Enrollment(student_id=auth.current_user.id, course_id=course.id)
            db.add(enrollment)
            db.commit()
            messagebox.showinfo("Success", f"Joined {course.title}!")
            self.code_entry.delete(0, tk.END)
            self.load_courses()
        finally:
            db.close()

    def leave_course(self, course_id, course_title):
        confirm = messagebox.askyesno("Leave Course", f"Are you sure you want to leave \"{course_title}\"?")
        if not confirm:
            return
        db = SessionLocal()
        try:
            enrollment = db.query(Enrollment).filter(
                Enrollment.student_id == auth.current_user.id,
                Enrollment.course_id == course_id
            ).first()
            if enrollment:
                db.delete(enrollment)
                db.commit()
                messagebox.showinfo("Success", f"You left \"{course_title}\"")
                self.load_courses()
        finally:
            db.close()

    def view_course(self, course_id):
        # We will create a new frame and put it in the controller container
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        screen = StudentCourseView(self.controller.container, self.controller, course_id)
        screen.pack(fill=tk.BOTH, expand=True)

    def logout(self):
        auth.logout()
        self.controller.show_login()

class StudentCourseView(ttk.Frame):
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
        ttk.Button(header, text="Back to Dashboard", command=self.controller.show_dashboard).pack(side=tk.LEFT)
        ttk.Label(header, text=self.course.title, style='Title.TLabel').pack(side=tk.LEFT, padx=20)
        
        # Body
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(body, text="Course Description:", font=('', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(body, text=self.course.description, wraplength=800).pack(anchor=tk.W, pady=(0, 20))
        
        ttk.Label(body, text="Tasks", style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        self.tasks_frame = ttk.Frame(body)
        self.tasks_frame.pack(fill=tk.BOTH, expand=True)
        self.load_tasks()
        
    def load_tasks(self):
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.course_id == self.course_id).all()
            if not tasks:
                ttk.Label(self.tasks_frame, text="No tasks available.").pack(anchor=tk.W)
            else:
                for t in tasks:
                    sub = db.query(Submission).filter(
                        Submission.task_id == t.id,
                        Submission.student_id == auth.current_user.id
                    ).first()
                    
                    frame = ttk.Frame(self.tasks_frame, style='Card.TFrame', padding=10)
                    frame.pack(fill=tk.X, pady=5)
                    
                    ttk.Label(frame, text=t.title, font=('', 12, 'bold'), style='Card.TLabel').pack(side=tk.LEFT)
                    
                    if sub:
                        status = f"Score: {sub.ai_score}/7" if sub.status == 'completed' else "Processing..."
                        ttk.Label(frame, text=status, style='Card.TLabel').pack(side=tk.RIGHT, padx=10)
                        ttk.Button(frame, text="View / Submit Again", command=lambda t_id=t.id: self.open_submission(t_id)).pack(side=tk.RIGHT)
                    else:
                        ttk.Button(frame, text="Submit", style='Primary.TButton', command=lambda t_id=t.id: self.open_submission(t_id)).pack(side=tk.RIGHT)
        finally:
            db.close()
            
    def open_submission(self, task_id):
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        screen = TaskSubmissionView(self.controller.container, self.controller, self.course_id, task_id)
        screen.pack(fill=tk.BOTH, expand=True)

class TaskSubmissionView(ttk.Frame):
    def __init__(self, parent, controller, course_id, task_id):
        super().__init__(parent)
        self.controller = controller
        self.course_id = course_id
        self.task_id = task_id
        self.file_path = None
        
        db = SessionLocal()
        self.task = db.query(Task).get(task_id)
        self.subs = db.query(Submission).filter(
            Submission.task_id == task_id,
            Submission.student_id == auth.current_user.id
        ).order_by(Submission.submitted_at.desc()).all()
        db.close()
        
        self.build_ui()
        
    def build_ui(self):
        # Header
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        btn = ttk.Button(header, text="Back to Course", 
                         command=lambda: self.return_to_course())
        btn.pack(side=tk.LEFT)
        ttk.Label(header, text=self.task.title, style='Title.TLabel').pack(side=tk.LEFT, padx=20)
        
        # Body
        body = ttk.Frame(self, padding=20)
        body.pack(fill=tk.BOTH, expand=True)
        
        # Task Description
        ttk.Label(body, text="Task Description:", font=('', 12, 'bold')).pack(anchor=tk.W)
        desc = tk.Text(body, height=5, wrap=tk.WORD, bg="white", fg="black")
        desc.insert(tk.END, self.task.description)
        desc.config(state=tk.DISABLED)
        desc.pack(fill=tk.X, pady=(0, 20))
        
        # Notebook for Tabs
        notebook = ttk.Notebook(body)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # New Submission Tab
        new_sub_tab = ttk.Frame(notebook, padding=10)
        notebook.add(new_sub_tab, text="Submit Answer")
        
        # Past Submissions Tab
        past_subs_tab = ttk.Frame(notebook, padding=10)
        notebook.add(past_subs_tab, text=f"Past Submissions ({len(self.subs)})")
        
        # Build New Submission UI
        ttk.Label(new_sub_tab, text="Text Answer:").pack(anchor=tk.W, pady=5)
        self.text_ans = tk.Text(new_sub_tab, height=10, wrap=tk.WORD, bg="white", fg="black")
        self.text_ans.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(new_sub_tab, text="OR Upload File (Image/PDF/TXT):").pack(anchor=tk.W)
        file_frame = ttk.Frame(new_sub_tab)
        file_frame.pack(fill=tk.X, pady=5)
        self.file_lbl = ttk.Label(file_frame, text="No file selected")
        self.file_lbl.pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.RIGHT)
        
        self.submit_btn = ttk.Button(new_sub_tab, text="Submit & Evaluate", style='Primary.TButton', command=self.submit)
        self.submit_btn.pack(pady=20, fill=tk.X)
        
        self.loading_lbl = ttk.Label(new_sub_tab, text="", font=('', 12, 'italic'))
        self.loading_lbl.pack(pady=10)
        
        # Build Past Submissions UI
        if not self.subs:
            ttk.Label(past_subs_tab, text="No past submissions.").pack(pady=20)
        else:
            past_text = tk.Text(past_subs_tab, wrap=tk.WORD, bg="white", fg="black")
            for idx, s in enumerate(self.subs):
                attempt_num = len(self.subs) - idx
                past_text.insert(tk.END, f"--- Attempt {attempt_num} ---\n")
                date_str = s.submitted_at.strftime("%Y-%m-%d %H:%M") if s.submitted_at else "Unknown"
                past_text.insert(tk.END, f"Date: {date_str}\n")
                if s.status == 'completed':
                    past_text.insert(tk.END, f"Grade: {s.ai_score}/7\n")
                    past_text.insert(tk.END, f"Feedback:\n{s.ai_feedback}\n\n")
                else:
                    past_text.insert(tk.END, f"Status: {s.status}\n\n")
            past_text.config(state=tk.DISABLED)
            past_text.pack(fill=tk.BOTH, expand=True)
            
    def return_to_course(self):
        for widget in self.controller.container.winfo_children():
            widget.destroy()
        screen = StudentCourseView(self.controller.container, self.controller, self.course_id)
        screen.pack(fill=tk.BOTH, expand=True)
            
    def browse_file(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            self.file_path = filepath
            import os
            self.file_lbl.config(text=os.path.basename(filepath))
            
    def submit(self):
        text_content = self.text_ans.get("1.0", tk.END).strip()
        if not text_content and not self.file_path:
            messagebox.showerror("Error", "Please provide a text answer or file.")
            return
            
        self.submit_btn.config(state=tk.DISABLED)
        self.loading_lbl.config(text="Uploading and waiting for AI evaluation... (This may take 10-30 seconds)")
        
        # Start background thread to avoid freezing GUI
        thread = threading.Thread(target=self._process_submission, args=(text_content,))
        thread.daemon = True
        thread.start()
        
    def _process_submission(self, text_content):
        # We need a new session for the thread
        db = SessionLocal()
        try:
            task = db.query(Task).get(self.task_id)
            
            # Prepare content
            submission_content = text_content
            file_name = None
            if self.file_path:
                import os
                import shutil
                file_name = os.path.basename(self.file_path)
                os.makedirs("uploads", exist_ok=True)
                dest = os.path.join("uploads", file_name)
                # Ensure filename is unique by prefixing time
                import time
                unique_name = f"{int(time.time())}_{file_name}"
                dest = os.path.join("uploads", unique_name)
                shutil.copy(self.file_path, dest)
                
                # Check ext
                ext = unique_name.rsplit('.', 1)[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    submission_content += f"\n[IMAGE_FILE:{dest}]"
                elif ext == 'txt':
                    with open(dest, 'r') as f:
                        submission_content += "\n\n" + f.read()
                        
            # Save empty submission first 
            sub = Submission(
                task_id=self.task_id, 
                student_id=auth.current_user.id,
                content=submission_content,
                file_name=file_name,
                status='processing'
            )
            db.add(sub)
            db.commit()
            
            # Call AI
            score, feedback = evaluate_submission_with_ai(task.description, submission_content, uploads_dir="uploads")
            
            # Update submission
            sub.ai_score = score
            sub.ai_feedback = feedback
            sub.status = 'completed' if isinstance(score, (int, float)) else 'error'
            db.commit()
            
            # Update UI on main thread
            self.controller.after(0, self._evaluation_done)
            
        except Exception as e:
            # Update UI on main thread with error
            self.controller.after(0, lambda: messagebox.showerror("Database error", str(e)))
        finally:
            db.close()
            
    def _evaluation_done(self):
        messagebox.showinfo("Success", "Task evaluation complete!")
        # Reload the view
        self.open_submission(self.task_id)
