from database import SessionLocal, User
from werkzeug.security import generate_password_hash, check_password_hash

class AuthManager:
    _instance = None
    _current_user = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthManager, cls).__new__(cls)
        return cls._instance

    @property
    def current_user(self):
        # We need to refresh the user object from the DB to ensure associations are loaded properly
        if self._current_user:
            db = SessionLocal()
            refreshed = db.query(User).get(self._current_user.id)
            db.close()
            return refreshed
        return None

    def login(self, email, password):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if user and check_password_hash(user.password_hash, password):
                self._current_user = user
                return True, "Success"
            return False, "Invalid email or password"
        except Exception as e:
            return False, f"Database error: {e}"
        finally:
            db.close()

    def register(self, first_name, last_name, email, password, role):
        db = SessionLocal()
        try:
            if db.query(User).filter(User.email == email).first():
                return False, "Email already exists"
                
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                is_approved=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            self._current_user = user
            return True, "Registration successful"
        except Exception as e:
            db.rollback()
            return False, f"Database error: {e}"
        finally:
            db.close()

    def logout(self):
        self._current_user = None

auth = AuthManager()
