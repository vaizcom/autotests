import os
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('URL')

# Загружает переменные окружения из .env
# ID тестовых сущностей — спейсы, проекты, борды, майлстоуны, документы.
CURRENT_SPACE_ID = os.getenv('CURRENT_SPACE_ID')
MAIN_SPACE_ID = os.getenv('MAIN_SPACE_ID')
SECOND_SPACE_ID = os.getenv('SECOND_SPACE_ID')
MAIN_PROJECT_ID = os.getenv('MAIN_PROJECT_ID')
MAIN_PROJECT_2_ID = os.getenv('MAIN_2_PROJECT_ID')
SECOND_PROJECT_ID = os.getenv('SECOND_PROJECT_ID')
MAIN_BOARD_ID = os.getenv('MAIN_BOARD_ID')
SECOND_BOARD_ID = os.getenv('SECOND_BOARD_ID')
BOARD_WITH_TASKS = os.getenv('BOARD_WITH_TASKS')
BOARD_FOR_TEST = os.getenv('BOARD_FOR_TEST')
SPACE_CLIENT = os.getenv('SPACE_CLIENT')
MILESTONE_1_ID = os.getenv('MILESTONE_1_ID')
MILESTONE_2_ID = os.getenv('MILESTONE_2_ID')

MAIN_SPACE_DOC_ID = os.getenv('MAIN_SPACE_DOC_ID')
MAIN_PROJECT_DOC_ID = os.getenv('MAIN_PROJECT_DOC_ID')
MAIN_PERSONAL_DOC_ID = os.getenv('MAIN_PERSONAL_DOC_ID')

# Учётные данные по ролям — email и пароль для каждой роли в тестовом спейсе.
USERS = {
    'project_client': {'email': os.getenv('PROJECT_CLIENT'), 'password': os.getenv('PASSWORD')},
    'space_client': {'email': SPACE_CLIENT, 'password': os.getenv('PASSWORD')},
    'foreign_client': {'email': os.getenv('FOREIGN_CLIENT'), 'password': os.getenv('PASSWORD')},
    'guest': {'email': os.getenv('GUEST_EMAIL'), 'password': os.getenv('PASSWORD')},
    'member': {'email': os.getenv('MEMBER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'manager': {'email': os.getenv('MANAGER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'owner': {'email': os.getenv('OWNER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'main': {'email': os.getenv('MAIN_CLIENT'), 'password': os.getenv('PASSWORD')},
    'second_main': {'email': os.getenv('SECOND_MAIN_CLIENT'), 'password': os.getenv('PASSWORD')},
}

TEST_STAND_NAME = os.getenv('TEST_STAND_NAME', 'kuber_dev')

# URL стенда — выбирается по TEST_STAND_NAME.
API_URL = {
    'dev': 'https://api.vaiz.dev/v4',
    'local': 'https://api.vaiz.local:10000/v4',
    'kuber_dev': 'https://vaiz-api-ms.vaiz.dev/v4',
    'kuber_uat': 'https://vaiz-api-uat.vaiz.dev/v4',
}[TEST_STAND_NAME]

PUBLIC_API_BASE_URL = os.getenv('PUBLIC_API_BASE_URL', 'https://api.vaiz.com')

# ID тестовых сущностей для Public API
PUBLIC_PROJECT_ID = os.getenv('PUBLIC_PROJECT_ID', '6a8d60e54c09ca59fa8e847a')
PUBLIC_TASK_ID = os.getenv('PUBLIC_TASK_ID', '6a8d61164c09ca59fa8ebf96')
PUBLIC_MILESTONE_ID = os.getenv('PUBLIC_MILESTONE_ID', '6a8d63164c09ca59fa913619')
PUBLIC_DOCUMENT_ID = os.getenv('PUBLIC_DOCUMENT_ID', '6a8d61994c09ca59fa8f848a')

