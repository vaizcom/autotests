## Тестовый фреймворк: описание

### Что тестируем

Веб-приложение для управления проектами (задачи, борды, документы, майлстоуны). Три направления тестирования: internal API (backend), UI (frontend), public API.

### Стек

**Язык:** Python. **Тестовый фреймворк:** pytest. **UI-автоматизация:** Playwright. **Отчёты:** Allure. **CI:** GitHub Actions. **БД:** MongoDB (для получения OTP в тестах авторизации).


### Архитектура по слоям (backend)

#### Слой 1. Конфигурация — `config/settings.py`

Загружает переменные окружения из `.env`. Определяет URL стенда, учётные данные по ролям, ID тестовых сущностей. Поддерживает несколько стендов:

```python
# config/settings.py

TEST_STAND_NAME = os.getenv('TEST_STAND_NAME', 'kuber_dev')

API_URL = {
    'dev': 'https://api.vaiz.dev/v4',
    'local': 'https://api.vaiz.local:10000/v4',
    'kuber_dev': 'https://vaiz-api-ms.vaiz.dev/v4',
    'kuber_uat': 'https://vaiz-api-uat.vaiz.dev/v4',
}[TEST_STAND_NAME]

USERS = {
    'owner':   {'email': os.getenv('OWNER_EMAIL'),   'password': os.getenv('PASSWORD')},
    'manager': {'email': os.getenv('MANAGER_EMAIL'), 'password': os.getenv('PASSWORD')},
    'member':  {'email': os.getenv('MEMBER_EMAIL'),  'password': os.getenv('PASSWORD')},
    'guest':   {'email': os.getenv('GUEST_EMAIL'),   'password': os.getenv('PASSWORD')},
    ...
}
```

Генераторы тестовых данных (`config/generators.py`) создают уникальные имена, slug'и, email'ы:

```python
# config/generators.py

def generate_space_name() -> str:
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f'space_{current_datetime}'   # → space_2026-09-06_14-30-45
```

---

#### Слой 2. Аутентификация — `core/auth.py`

Единая точка логина. Двухшаговая аутентификация: получает временный JWT (`tempToken`), обменивает его с паролем на рабочий JWT (`authToken`). Токены кешируются по ролям — логин происходит один раз за сессию:

```python
# core/auth.py

def get_token(role: str = 'guest') -> str:
    if role in _token_cache:
        return _token_cache[role]

    credentials = USERS.get(role)
    # Шаг 1: AuthWithEmail → tempToken
    resp = requests.post(f"{base_url}/AuthWithEmail",
                         json={"email": credentials['email']})
    temp_token = resp.json()["payload"]["tempToken"]

    # Шаг 2: VerifyPassword → authToken
    resp = requests.post(f"{base_url}/VerifyPassword",
                         json={"tempToken": temp_token, "password": credentials['password']})
    token = resp.json()["payload"]["authToken"]

    _token_cache[role] = token
    return token
```

Если логинка поменяется (URL, формат, поля) — правится только этот файл.

---

#### Слой 3. Транспортный слой — `core/client.py`

`APIClient` — обёртка над `requests.Session`. Подставляет токен в заголовки, делает retry, управляет таймаутами. Не знает про бизнес-логику:

```python
# core/client.py

class APIClient:
    def __init__(self, base_url: str, token: str = None):
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=2,
                      status_forcelist=[429, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        if token:
            self.set_auth_header(token)

    def set_auth_header(self, token: str):
        self.session.headers.update({
            'Authorization': f'Bearer {token}',  # стандарт API
            'Cookie': f'_t={token}',              # совместимость с фронтом
        })

    def post(self, path, json=None, headers=None, timeout=(5, 30), **kwargs):
        url = f'{self.base_url}{path}'
        return self.session.post(url, json=json, headers=headers, timeout=timeout)
```

Internal API использует только POST (RPC-стиль): `/CreateTask`, `/GetTask`, `/DeleteTask`.

---

#### Слой 4. Endpoint-функции — `test_backend/data/endpoints/`

20 модулей по сущностям (Task, Board, Project, Document, Space и др.). Каждая функция формирует словарь `{path, json, headers}` — знает формат запроса, но не знает про клиент:

```python
# test_backend/data/endpoints/Task/task_endpoints.py

def create_task_endpoint(space_id, board, name=None, assignees=None, ...) -> dict:
    payload = {"board": board, "name": name or "Untitled task"}
    if assignees: payload["assignees"] = assignees
    ...
    return {
        "path": "/CreateTask",
        "json": payload,
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id},
    }

def get_task_endpoint(space_id, slug_id) -> dict:
    return {
        "path": "/GetTask",
        "json": {"slugId": slug_id},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id},
    }
```

Связка с транспортным слоем через распаковку:

```python
client.post(**create_task_endpoint(name="test", board=board_id, space_id=space_id))
```

Там же лежат assert-хелперы для проверки структуры ответа (`multiaction_asserts.py`, `assert_task_payload.py`).

---

#### Слой 5. Фикстуры — `conftest.py`

Трёхуровневая иерархия:

**`tests/conftest.py`** — shared-инфраструктура (MongoDB, SSL, allure):
```python
@pytest.fixture(scope="session")
def db(mongo_client):
    return mongo_client[os.getenv("MONGO_DB_NAME")]
```

**`tests/test_backend/conftest.py`** — все backend-фикстуры:
```python
# Клиенты по ролям
@pytest.fixture(scope='session')
def owner_client():
    return APIClient(base_url=API_URL, token=get_token('owner'))

# Тестовые сущности
@pytest.fixture(scope='session')
def main_space(main_client) -> str:
    assert MAIN_SPACE_ID, 'Не задана переменная окружения MAIN_SPACE_ID'
    resp = main_client.post(**get_space_endpoint(space_id=MAIN_SPACE_ID))
    assert resp.status_code == 200
    return MAIN_SPACE_ID

# Фабрики
@pytest.fixture
def make_task_in_main(owner_client, main_space, main_board):
    created_ids = []
    def _create_task(body_overrides: dict):
        resp = owner_client.post(**create_task_endpoint(**body))
        task = resp.json()["payload"]["task"]
        created_ids.append(task["_id"])
        return task
    yield _create_task
    for tid in created_ids:   # teardown — удаление
        owner_client.post(**delete_task_endpoint(task_id=tid, space_id=main_space))
```

**Модульные conftest.py** — фикстуры конкретного сьюта (например `history/conftest.py`).

Скоупы: `session` для долгоживущих сущностей (клиенты, спейсы), `module` и `function` для изолированных.

---

#### Слой 6. Тесты

Паттерн backend-теста — 4 шага, каждый в `allure.step()`:

```python
# test_backend/multiaction/move/test_move.py

@allure.parent_suite("Multiaction")
@allure.suite("Move")
@allure.sub_suite("Positive")
@allure.title("Move: переместить задачи в другую группу")
def test_move_tasks_to_another_group(
    owner_client, main_space, make_task_in_main, temp_board_in_main, board_groups,
):
    target_group = board_groups["Todo"]

    # 1. Pre-condition — создаём задачи (попадают в Backlog)
    with allure.step("Создаём 2 задачи (попадают в Backlog)"):
        tasks = [make_task_in_main({"name": f"move-test-{i}", "board": temp_board_in_main})
                 for i in range(2)]
        task_ids = [t["_id"] for t in tasks]

    # 2. Action — перемещаем
    with allure.step("Перемещаем в группу Todo"):
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=task_ids,
            board_id=temp_board_in_main, to_group_id=target_group,
        ))

    # 3. Check response — контракт ответа
    with allure.step("Проверяем контракт ответа"):
        payload = assert_multiaction_response(resp)

    with allure.step("Проверяем, что все задачи в success"):
        assert sorted(payload["success"]) == sorted(task_ids)
        assert payload["failed"] == []
        assert payload["skipped"] == []

    # 4. Post-condition — подтверждаем изменения через GetTask
    with allure.step("Проверяем через GetTask, что задачи в группе Todo"):
        for tid in task_ids:
            r = owner_client.post(**get_task_endpoint(space_id=main_space, slug_id=tid))
            assert r.status_code == 200
            task = r.json()["payload"]["task"]
            assert task["group"] == target_group
```

Негативный тест — проверка ошибки:

```python
# test_backend/multiaction/move/test_move.py

@allure.title("Move: невалидный to_group_id -> ошибка")
def test_move_invalid_group_id(owner_client, main_space, make_task_in_main, temp_board_in_main):
    fake_group_id = generate_object_id()

    with allure.step("Создаём задачу"):
        task = make_task_in_main({"name": "move-neg-group", "board": temp_board_in_main})

    with allure.step("Перемещаем с несуществующей группой"):
        resp = owner_client.post(**multiple_move_tasks_endpoint(
            space_id=main_space, tasks_ids=[task["_id"]],
            board_id=temp_board_in_main, to_group_id=fake_group_id,
        ))

    with allure.step("Проверяем ошибку 400 IncorrectToGroupId"):
        assert resp.status_code == 400
        error = resp.json().get("error", {})
        assert error.get("code") == "IncorrectToGroupId"
```

---

### Дополнительная инфраструктура

**`core/waiters.py`** — поллинг с таймаутом для ожидания асинхронных изменений:
```python
def wait_until(condition_func, timeout=10, poll_interval=0.5, error_msg="..."):
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = condition_func()
        if result:
            return result
        time.sleep(poll_interval)
    raise TimeoutError(error_msg)
```

**`core/response_utils.py`** — форматирование ответов для assert-сообщений. Парсит HTML (Cloudflare 504), JSON-ошибки, обрезает длинные ответы.

**Хуки pytest:**
- `pytest_configure` (корневой conftest) — разделение allure-отчётов по сьютам
- `pytest_collection_finish` (test_backend conftest) — проверка доступности стенда перед запуском, чтобы не ждать таймаутов на каждом тесте

**CI** — три отдельных воркфлоу в `.github/workflows/`: `backend_tests.yml`, `frontend_tests.yml`, `public_api_tests.yml`. Allure-отчёты публикуются на GitHub Pages.

---

### Public API

Отдельный сьют со своим клиентом (`PublicAPIClient`, REST, GET-запросы, PAT-токен). Покрывает: history (фильтры, пагинация, структура ответа), авторизацию, rate-limit. Autouse-фикстура `rate_limit` добавляет паузу 1 сек между запросами для соблюдения лимита 1 rps.

---

### Принципы

- **Разделение слоёв** — endpoint не знает про клиент, клиент не знает про бизнес-логику
- **Единая точка изменения** — логинка поменялась → правим только `core/auth.py`
- **Нет хардкода** — тестовые данные из `.env` и генераторов
- **Cleanup** — через фикстуры с teardown (backend) и `test_99` (frontend)
- **Allure-отчёты** — `parent_suite → suite → sub_suite` для навигации, каждый шаг в `allure.step()`

---

### Ключевые понятия

- **JWT (JSON Web Token)** — формат токена (header.payload.signature в base64). Содержит ID пользователя, срок жизни (поле `exp`). Не шифрован — только подписан
- **Bearer** — способ передачи токена в HTTP-заголовке (`Authorization: Bearer <token>`)
- **tempToken** — временный JWT, выдаётся после AuthWithEmail, нужен только для подтверждения OTP/пароля
- **authToken** — рабочий JWT, с ним клиент ходит во все эндпоинты API
- **PAT (Personal Access Token)** — долгоживущий токен для public API, создаётся пользователем вручную
- **Хук pytest** — функция с зарезервированным именем, которую pytest вызывает автоматически в нужный момент жизненного цикла. Действует в папке, где расположен conftest.py
- **Webhook** — HTTP-запрос, который одна система автоматически отправляет другой при событии (например GitHub → CI при push)
