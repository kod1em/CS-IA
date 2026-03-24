import tkinter as tk
from tkinter import ttk
from ui.styles import setup_styles
from core.auth import auth

class StudySystemApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("StudySystem Desktop")
        self.geometry("1200x900")
        self.minsize(740, 600)
        
        # Initialize styles
        setup_styles()
        
        # Configure main window layout
        self.configure(bg="#f4f6f9")
        
        # Container frame that holds the current screen
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Show Login by default
        self.show_login()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self._clear_container()
        from ui.auth_ui import LoginScreen
        screen = LoginScreen(self.container, self)
        screen.pack(fill=tk.BOTH, expand=True)

    def show_register(self):
        self._clear_container()
        from ui.auth_ui import RegisterScreen
        screen = RegisterScreen(self.container, self)
        screen.pack(fill=tk.BOTH, expand=True)

    def show_dashboard(self):
        self._clear_container()
        user = auth.current_user
        if not user:
            self.show_login()
            return
            
        if user.role == "teacher":
            from ui.teacher_ui import TeacherDashboard
            screen = TeacherDashboard(self.container, self)
        else:
            from ui.student_ui import StudentDashboard
            screen = StudentDashboard(self.container, self)
            
        screen.pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    app = StudySystemApp()
    app.mainloop()
