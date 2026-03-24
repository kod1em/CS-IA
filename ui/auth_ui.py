import tkinter as tk
from tkinter import ttk, messagebox
from core.auth import auth

class BaseScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Center the main card
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)

class LoginScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        card = ttk.Frame(self, style='Card.TFrame', padding=30)
        card.grid(row=1, column=1)
        
        # Title
        ttk.Label(card, text="System Login", style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Error Label
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(card, textvariable=self.error_var, style='Error.TLabel')
        self.error_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Email
        ttk.Label(card, text="Email", style='Card.TLabel').grid(row=2, column=0, sticky='w', pady=5)
        self.email_entry = ttk.Entry(card, width=30)
        self.email_entry.grid(row=2, column=1, pady=5)
        
        # Password
        ttk.Label(card, text="Password", style='Card.TLabel').grid(row=3, column=0, sticky='w', pady=5)
        self.password_entry = ttk.Entry(card, width=30, show="*")
        self.password_entry.grid(row=3, column=1, pady=5)
        
        # Login Button
        login_btn = ttk.Button(card, text="Login", style='Primary.TButton', command=self.attempt_login)
        login_btn.grid(row=4, column=0, columnspan=2, sticky='we', pady=(20, 10))
        
        # Switch to Register
        link_frame = ttk.Frame(card, style='Card.TFrame')
        link_frame.grid(row=5, column=0, columnspan=2)
        
        ttk.Label(link_frame, text="Don't have an account?", style='Card.TLabel').pack(side=tk.LEFT)
        reg_btn = ttk.Button(link_frame, text="Register", command=controller.show_register)
        reg_btn.pack(side=tk.LEFT, padx=(5, 0))

    def attempt_login(self):
        email = self.email_entry.get().strip()
        pwd = self.password_entry.get()
        
        if not email or not pwd:
            self.error_var.set("Please fill in all fields.")
            return
            
        success, msg = auth.login(email, pwd)
        if success:
            self.controller.show_dashboard()
        else:
            self.error_var.set(msg)

class RegisterScreen(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        card = ttk.Frame(self, style='Card.TFrame', padding=30)
        card.grid(row=1, column=1)
        
        ttk.Label(card, text="Create Account", style='Title.TLabel').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        self.error_var = tk.StringVar()
        ttk.Label(card, textvariable=self.error_var, style='Error.TLabel').grid(row=1, column=0, columnspan=2)
        
        # Fields
        fields = [
            ("First Name", "first_name"),
            ("Last Name", "last_name"),
            ("Email", "email"),
            ("Password", "password"),
            ("Confirm Password", "confirm_password")
        ]
        
        self.entries = {}
        for idx, (label_text, key) in enumerate(fields):
            row = idx + 2
            ttk.Label(card, text=label_text, style='Card.TLabel').grid(row=row, column=0, sticky='w', pady=5, padx=5)
            
            show_char = "*" if "password" in key else ""
            entry = ttk.Entry(card, width=30, show=show_char)
            entry.grid(row=row, column=1, pady=5, padx=5)
            self.entries[key] = entry
            
        # Role selection
        row = len(fields) + 2
        ttk.Label(card, text="Role", style='Card.TLabel').grid(row=row, column=0, sticky='w', pady=5, padx=5)
        
        self.role_var = tk.StringVar(value="student")
        role_frame = ttk.Frame(card, style='Card.TFrame')
        role_frame.grid(row=row, column=1, sticky='w')
        ttk.Radiobutton(role_frame, text="Student", variable=self.role_var, value="student").pack(side=tk.LEFT, padx=(0,10))
        ttk.Radiobutton(role_frame, text="Teacher", variable=self.role_var, value="teacher").pack(side=tk.LEFT)
        
        # Submit Button
        submit_btn = ttk.Button(card, text="Register", style='Primary.TButton', command=self.attempt_register)
        submit_btn.grid(row=row+1, column=0, columnspan=2, sticky='we', pady=(20, 10))
        
        # Switch to Login
        link_frame = ttk.Frame(card, style='Card.TFrame')
        link_frame.grid(row=row+2, column=0, columnspan=2)
        ttk.Label(link_frame, text="Already have an account?", style='Card.TLabel').pack(side=tk.LEFT)
        ttk.Button(link_frame, text="Login", command=controller.show_login).pack(side=tk.LEFT, padx=(5, 0))

    def attempt_register(self):
        data = {k: v.get().strip() for k, v in self.entries.items()}
        role = self.role_var.get()
        
        if not all([data['first_name'], data['last_name'], data['email'], data['password'], data['confirm_password']]):
            self.error_var.set("Please fill all fields.")
            return
            
        if data['password'] != data['confirm_password']:
            self.error_var.set("Passwords do not match.")
            return
            
        success, msg = auth.register(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            role=role
        )
        
        if success:
            self.controller.show_dashboard()
        else:
            self.error_var.set(msg)
