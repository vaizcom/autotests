from os import environ

from dotenv import load_dotenv

load_dotenv()

# BASE_URL = environ.get('BASE_URL', default=f'https://dev:jaichoof8iigeech4upegooraeChooz1hoo9eece@app.vaiz.dev')
BASE_URL = environ.get('BASE_URL', default='https://vaiz-app-ms.vaiz.dev/')

URL = environ.get('URL', default='https://vaiz-api-ms.vaiz.dev/v3')
