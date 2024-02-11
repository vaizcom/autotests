from os import environ

from dotenv import load_dotenv

load_dotenv()

BASE_URL = environ.get('BASE_URL', default='https://app.vaiz.dev/')
