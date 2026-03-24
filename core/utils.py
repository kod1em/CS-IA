import uuid
from datetime import datetime

def generate_invitation_code():
    return str(uuid.uuid4())[:8].upper()

def convert_to_ib_grade(percentage):
    if percentage >= 90:
        return 7
    elif percentage >= 80:
        return 6
    elif percentage >= 70:
        return 5
    elif percentage >= 60:
        return 4
    elif percentage >= 45:
        return 3
    elif percentage >= 25:
        return 2
    elif percentage > 0:
        return 1
    else:
        return 0
