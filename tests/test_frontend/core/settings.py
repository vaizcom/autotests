from os import environ
from dotenv import load_dotenv

load_dotenv()

BASE_URL = environ.get("FRONTEND_URL", default="https://app.vaiz.com")
FRONTEND_EMAIL = environ.get("FRONTEND_EMAIL")
FRONTEND_PASSWORD = environ.get("FRONTEND_PASSWORD")
