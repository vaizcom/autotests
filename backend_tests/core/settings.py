from os import environ

from dotenv import load_dotenv

load_dotenv()

API_URL = environ.get('API_URL')
