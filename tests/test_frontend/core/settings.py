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

AUTOTEST_SPACE_NAME = "Autotest Space"
AUTOTEST_PROJECT_NAME = "Autotest Project"
AUTOTEST_MEMBER_EMAIL = environ.get("AUTOTEST_MEMBER_EMAIL", "mastretsovaone+main@gmail.com")

# Фиксированные ID сущностей для тестов (борда создаётся один раз вручную)
AUTOTEST_SPACE_ID = {
    "dev": "69eb40574942cdc3cd91a9df",
    "prod": "687655d8e38db1f0877954fa",
}[FRONTEND_STAND]

AUTOTEST_PROJECT_ID = {
    "dev": "69eb40a74942cdc3cd91aab8",
    "prod": "69f1d23f309d2c55d510eddf",
}[FRONTEND_STAND]

AUTOTEST_BOARD_ID = {
    "dev": "69f1f33d75af2693b6652325",
    "prod": "69f1d25b309d2c55d510f174",
}[FRONTEND_STAND]

AUTOTEST_BOARD_URL = f"{BASE_URL}/{AUTOTEST_SPACE_ID}/p/{AUTOTEST_PROJECT_ID}/b/{AUTOTEST_BOARD_ID}"
