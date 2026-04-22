from os import environ
from dotenv import load_dotenv

load_dotenv()

FRONTEND_STAND = environ.get("FRONTEND_STAND", "dev")

BASE_URL = {
    "prod": "https://app.vaiz.com",
    "dev": "https://app.vaiz.dev",
}[FRONTEND_STAND]

FRONTEND_EMAIL = environ.get("FRONTEND_EMAIL") or environ.get("OWNER_EMAIL")
FRONTEND_PASSWORD = environ.get("FRONTEND_PASSWORD") or environ.get("PASSWORD")
