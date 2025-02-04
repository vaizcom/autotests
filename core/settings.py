from os import environ

from dotenv import load_dotenv

load_dotenv()

# BASE_URL = environ.get('BASE_URL', default=f'https://dev:jaichoof8iigeech4upegooraeChooz1hoo9eece@app.vaiz.dev')
BASE_URL = environ.get('BASE_URL', default='https://app.vaiz.dev/')

API_URL = environ.get('API_URL', default='https://api.vaiz.dev/v2')
