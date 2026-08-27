# CLAUDE.md

## Язык общения
Всегда общаться на русском.

## Структура проекта
- `tests/test_frontend/` — Playwright E2E тесты (pytest + allure)
- `tests/test_backend/` — API тесты (pytest + allure)
- `tests/test_public_api/` — Public API тесты (PAT-авторизация)
- `.github/workflows/` — CI воркфлоу (frontend_tests.yml, backend_tests.yml, public_api_tests.yml)
- `tests/config/settings.py` — загрузка `.env` → `USERS`, `API_URL`
- `tests/core/` — общая инфраструктура: `auth.py` (токены), `client.py` (HTTP-клиент с retry), `waiters.py`

## Backend-тесты: архитектура

### Эндпоинты
- Лежат в `tests/test_backend/data/endpoints/` — по модулю на каждую сущность
- Каждый эндпоинт — функция, возвращающая dict: `{"path": ..., "json": ..., "headers": ...}`
- Вызываются через `client.post(**endpoint_function(...))`

### Фикстуры
- Корневой `tests/conftest.py` — клиенты всех ролей (`main_client`, `manager_client`, `member_client`, `guest_client` и т.д.), спейсы, проекты, борды
- Модульные `conftest.py` — фикстуры конкретного тест-модуля (например `access_group/conftest.py`)
- Скоуп `session` — сущности создаются один раз на сессию, не пересоздаются между тестами

### Паттерн тестов
1. **Pre-condition** — `GetAccessGroup` / `GetTask` и т.д. для проверки начального состояния
2. **Action** — вызов тестируемого эндпоинта
3. **Check response** — проверка статуса и тела ответа
4. **Post-condition** — повторный Get-запрос для подтверждения изменений в БД (не «персистентность», а «Post-condition»)

Каждый шаг обёрнут в `with allure.step(...)`.

## Frontend-тесты: архитектура
- Единое флоу: `test_01` (сетап) → тесты → `test_99` (клинап)
- Cleanup всегда в `test_99`, не внутри теста — чтобы отработал при падении
- Setup/cleanup — в хелперы, не dependency-цепочки
- Локаторы: `tests/test_frontend/core/locators.py`

## Conventions
- Allure: `@allure.parent_suite → @allure.suite → @allure.sub_suite`
- Хелперы с expect перед каждым действием (click/fill) — иначе CI падает
- `pytest.ini` — CI конфиг (без --headed/--slowmo), локальные дефолты в conftest через `CI` env var
- `is_dependency` в soft_step — hard fail только для тестов с `name=`, не для `depends=`
- Reload только при навигации между страницами, inline-действия — expect с таймаутом
- Не смешивать archive/history в тесты сущностей — это отдельные сьюты

## Коммиты и пуш
- `pytest --collect-only` перед каждым коммитом — проверка что импорты не сломались
- Не пушить без явного запроса пользователя — "коммить" = только commit
- Всегда через feature-ветку, не в main напрямую
- Использовать `Edit` вместо `Write` — не затирать ручные изменения

## Troubleshooting
- **Бродкаст/реактивность на фронте:** Запустить мануально "Staging × Static Assets" в основном репозитории Vaiz
- **Счётчики подзадач не обновляются:** Известный баг бродкаста, тесты ловят через soft checks (test_11 — _check_counter, test_12/13 — soft_step)
