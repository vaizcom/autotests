from dotenv import load_dotenv
load_dotenv()
import os

API_URL = os.getenv("API_URL")
print("Loaded API_URL:", API_URL)
CURRENT_SPACE_ID = os.getenv("CURRENT_SPACE_ID")

USERS = {
    "guest": {
        "email": os.getenv("GUEST_EMAIL"),
        "password": os.getenv("PASSWORD")
    },
    "member": {
        "email": os.getenv("MEMBER_EMAIL"),
        "password": os.getenv("PASSWORD")
    },
    "manager": {
        "email": os.getenv("MANAGER_EMAIL"),
        "password": os.getenv("PASSWORD")
    },
    "owner": {
        "email": os.getenv("OWNER_EMAIL"),
        "password": os.getenv("PASSWORD")
    }
}


