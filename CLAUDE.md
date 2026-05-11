# CLAUDE.md

## Язык общения
Всегда общаться на русском.

## Структура проекта
- `tests/test_frontend/` — Playwright E2E тесты (pytest + allure)
- `tests/test_backend/` — API тесты (pytest + allure)
- `.github/workflows/` — CI воркфлоу (frontend_tests.yml, backend_tests.yml)

## Conventions
- Allure: `@allure.parent_suite → @allure.suite → @allure.sub_suite`
- Хелперы с expect перед каждым действием (click/fill) — иначе CI падает
- `pytest.ini` — CI конфиг (без --headed/--slowmo), локальные дефолты в conftest через `CI` env var
- `is_dependency` в soft_step — hard fail только для тестов с `name=`, не для `depends=`
- Reload только при навигации между страницами, inline-действия — expect с таймаутом

## Troubleshooting
- **Бродкаст/реактивность на фронте:** Запустить мануально "Staging × Static Assets" в основном репозитории Vaiz
- **Счётчики подзадач не обновляются:** Известный баг бродкаста, тесты ловят через soft checks (test_11 — _check_counter, test_12/13 — soft_step)
