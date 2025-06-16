import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('URL')
print('Loaded URL:', URL)

CURRENT_SPACE_ID = os.getenv('CURRENT_SPACE_ID')

USERS = {
    'guest': {'email': os.getenv('GUEST_EMAIL'), 'password': os.getenv('PASSWORD')},
    'member': {'email': os.getenv('MEMBER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'manager': {'email': os.getenv('MANAGER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'owner': {'email': os.getenv('OWNER_EMAIL'), 'password': os.getenv('PASSWORD')},
}

TEST_STAND_NAME = os.getenv('TEST_STAND_NAME', 'kuber_dev')

API_URL = {
    'dev': 'https://api.vaiz.dev/v4',
    'uat': 'https://uat--api.vaiz.dev/v4',
    'kuber_dev': 'https://vaiz-api-ms.vaiz.dev/v4',
    'kuber_uat': 'https://vaiz-api-uat.vaiz.dev/v4',
}[TEST_STAND_NAME]

if os.getenv('GITHUB_ENV'):
    with open(os.getenv('GITHUB_ENV'), 'a') as f:
        f.write(f'API_URL={API_URL}\n')
