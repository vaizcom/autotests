# Передача проекта автотестов VAIZ

## 1. Доступы

### Gmail-аккаунт (основной)

Все тестовые пользователи — алиасы одного Gmail-аккаунта:

- **Email:** `mastretsovaone@gmail.com`
- **Пароль:** `VaizAutoTests2026`

При получении аккаунта:
1. Сменить пароль
2. Убрать/заменить резервный email и телефон на свои
3. Отключить или перенастроить 2FA
4. Выйти из всех активных сессий (Google → Безопасность → Управление устройствами)

### Тестовые пользователи на стендах

Все аккаунты используют общий пароль `123456` для входа в Vaiz.

| Роль в тестах | Email | Ключ в USERS |
|---------------|-------|--------------|
| Основной клиент | `mastretsovaone+main@gmail.com` | `main` |
| Второй основной | `mastretsovaone+second_main@gmail.com` | `second_main` |
| Owner | `mastretsovaone+owner@gmail.com` | `owner` |
| Manager | `mastretsovaone+manager@gmail.com` | `manager` |
| Member | `mastretsovaone+member@gmail.com` | `member` |
| Guest | `mastretsovaone+guest@gmail.com` | `guest` |
| Чужой пользователь | `mastretsovaone+foreign@gmail.com` | `foreign_client` |
| Space Member | `mastretsovaone+space+memb@gmail.com` | `space_client` |
| Project Member | `mastretsovaone+project+memb@gmail.com` | `project_client` |
| Frontend | `mastretsovaone@gmail.com` | _(отдельно)_ |
| Public API | `mastretsovaone+publicapi@gmail.com` | _(PAT)_ |

Конфигурация: `tests/config/settings.py` читает из `.env`.

### Public API

- **PAT:** указан в `.env` (`PUBLIC_API_PAT`)
- **Space ID:** `6a8d5a4a4c09ca59fa861b79`
- PAT привязан к аккаунту `mastretsovaone+publicapi@gmail.com`
- Управление PAT: настройки пользователя в Vaiz UI

### GitHub

- **Репозиторий:** `vaizcom/autotests`
- **GitHub Pages (отчёты):**
  - Frontend: https://vaizcom.github.io/autotests/frontend/
  - Backend: https://vaizcom.github.io/autotests/backend/
  - Public API: https://vaizcom.github.io/autotests/public_api/

### CI Secrets (GitHub Actions → Settings → Secrets)

| Secret | Описание |
|--------|----------|
| `FRONTEND_EMAIL` | Email для фронтенд-тестов |
| `FRONTEND_PASSWORD` | Пароль для фронтенд-тестов |
| `CF_TOKEN` | Cloudflare WARP токен (VPN для dev-стенда) |
| `CF_TOKEN_NAME` | Имя Cloudflare токена (Variable, не Secret) |

Все переменные из `.env` также продублированы в GitHub Secrets для CI.

### MongoDB

- **URI:** указан в `.env` (`MONGO_URI`)
- **База:** `mongodb-staging`
- Используется для получения OTP при создании временных пользователей (`temp_client`)

---

## 2. Структура проекта

```
autotests/
├── .env                          # Креды и ID сущностей (НЕ в git)
├── .github/workflows/            # CI воркфлоу
│   ├── backend_tests.yml         # Бекенд тесты
│   ├── frontend_tests.yml        # Фронтенд тесты (Playwright)
│   └── public_api_tests.yml      # Public API тесты
├── docs/                         # Документация
├── Makefile                      # make debug, make lint, make report
├── pytest.ini                    # Конфиг pytest
├── requirements.txt              # Зависимости Python
├── CLAUDE.md                     # Инструкции для AI-ассистента
└── tests/
    ├── conftest.py               # Корневые фикстуры (клиенты, спейсы, борды)
    ├── config/
    │   ├── settings.py           # Загрузка .env → USERS, API_URL
    │   └── generators.py         # Генераторы slug и т.д.
    ├── core/
    │   ├── auth.py               # get_token() — авторизация + кэш
    │   ├── client.py             # APIClient — HTTP-клиент с retry
    │   ├── response_utils.py     # Утилиты для ответов
    │   └── waiters.py            # Polling/ожидание
    ├── test_backend/             # ~328 тест-файлов
    │   ├── access_group/         # Группы доступа и роли
    │   ├── authServis/           # Авторизация
    │   ├── billing/              # Биллинг
    │   ├── board/                # Борды
    │   ├── comment/              # Комментарии
    │   ├── document/             # Документы
    │   ├── history/              # История событий
    │   ├── invite/               # Инвайты
    │   ├── multiaction/          # Массовые операции
    │   ├── project/              # Проекты
    │   ├── space/                # Спейсы
    │   ├── task_service/         # Задачи
    │   └── data/endpoints/       # Эндпоинты (payload-билдеры)
    ├── test_frontend/            # ~35 тест-файлов (Playwright)
    │   ├── tests/
    │   │   ├── auth/             # Логин, регистрация, выход
    │   │   ├── smoke/            # Смоук-тесты
    │   │   ├── tasks/            # CRUD задач, поля
    │   │   ├── spaces/           # Спейсы
    │   │   └── milestones/       # Майлстоуны
    │   └── core/
    │       ├── locators.py       # Page Object локаторы
    │       └── settings.py       # Frontend-конфиг
    └── test_public_api/          # ~40 тест-файлов
        ├── conftest.py           # PublicAPIClient с PAT
        ├── history/              # GetHistory тесты
        └── data/                 # Эндпоинты public API
```

---

## 3. Стенды

| Стенд | API URL | Когда использовать |
|-------|---------|-------------------|
| `dev` | `https://api.vaiz.dev/v4` | Основная разработка |
| `kuber_dev` | `https://vaiz-api-ms.vaiz.dev/v4` | Kubernetes dev |
| `kuber_uat` | `https://vaiz-api-uat.vaiz.dev/v4` | UAT |
| `local` | `https://api.vaiz.local:10000/v4` | Локальный стенд |
| Production (public API) | `https://api.vaiz.com/public/v1` | Только public API |

Frontend:
- Dev: `https://app.vaiz.dev` (нужен VPN — см. ниже)
- Prod: `https://app.vaiz.com`

Стенд выбирается через `TEST_STAND_NAME` в `.env`.

### VPN для dev-стенда (Cloudflare Zero Trust)

Dev-стенд (`*.vaiz.dev`) закрыт за Cloudflare Zero Trust. Без VPN — недоступен.

**Локально:**
1. Установить [Cloudflare WARP](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/download-warp/)
2. Открыть WARP → Settings → Account → Login to Cloudflare Zero Trust
3. Организация: `vaiz`
4. Авторизоваться через корпоративный SSO

**В CI (уже настроено):**
- GitHub Action: `Boostport/setup-cloudflare-warp@v1.6.0` (`.github/actions/cloudflare/action.yml`)
- Service token: `CF_TOKEN_NAME` (GitHub Variable) + `CF_TOKEN` (GitHub Secret)
- Эти креды выдаёт DevOps-команда Vaiz

---

## 4. Установка с нуля (PyCharm + Mac)

### Шаг 1: Установить инструменты

```bash
# Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.11+
brew install python

# Allure (для отчётов)
brew install allure

# Git (если не установлен)
brew install git
```

### Шаг 2: Установить PyCharm

1. Скачать [PyCharm Community](https://www.jetbrains.com/pycharm/download/) (бесплатная) или Professional
2. Установить и запустить

### Шаг 3: Склонировать проект

```bash
cd ~/PycharmProjects
git clone git@github.com:vaizcom/autotests.git
```

Или в PyCharm: File → New → Project from Version Control → вставить URL репозитория.

### Шаг 4: Настроить Python Interpreter

1. PyCharm → Settings (Cmd+,) → Project → Python Interpreter
2. Add Interpreter → Add Local Interpreter → Virtualenv
3. Base interpreter: Python 3.11 (`/opt/homebrew/bin/python3` или `which python3`)
4. Location: оставить дефолтное (`.venv` внутри проекта)
5. OK → подождать пока создастся

### Шаг 5: Установить зависимости

В терминале PyCharm (Alt+F12):

```bash
pip install -r requirements.txt
playwright install
```

Или PyCharm сам предложит установить зависимости при открытии `requirements.txt`.

### Шаг 6: `.env`

Файл `.env` уже лежит в репозитории — после клонирования всё готово. Содержит креды тестовых аккаунтов, ID сущностей на стендах, MongoDB URI. Описание переменных — см. раздел "Доступы" выше.

### Шаг 7: Настроить pytest в PyCharm

1. Settings → Tools → Python Integrated Tools → Testing → Default test runner: **pytest**
2. Settings → Tools → Python Integrated Tools → Docstring format: по вкусу
3. Run → Edit Configurations → добавить pytest конфигурацию:
   - Working directory: корень проекта
   - Additional arguments: `-v --alluredir=allure-results`

### Шаг 8: Проверить что всё работает

```bash
# Проверка импортов (ничего не запускает)
pytest --collect-only tests/test_backend/access_group/

# Запустить один тест
pytest tests/test_backend/access_group/test_custom_group.py::test_update_custom_group_rights_on_space -v
```

### Шаг 9: VPN для dev-стенда

Если тесты идут на dev — нужен Cloudflare WARP (см. раздел "VPN для dev-стенда" выше).

---

## 5. Запуск тестов

### Локальный запуск

```bash
# Все бекенд-тесты
pytest tests/test_backend/ -m backend

# Конкретный файл
pytest tests/test_backend/access_group/test_custom_group.py -v

# Один тест
pytest tests/test_backend/access_group/test_custom_group.py::test_update_custom_group_rights_on_space -v

# Фронтенд (headed + slowmo)
pytest tests/test_frontend/tests/smoke/ -m frontend

# Отладка с сетапом и клинапом
make debug FILE=tests/test_frontend/tests/tasks/test_task_fields.py TEST=test_12
```

Или в PyCharm: правый клик на файл/тест → Run.

### CI (GitHub Actions)

- **Автоматически:** при push/PR в `main` — запускаются тесты по изменённым файлам
- **Вручную:** Actions → выбрать workflow → Run workflow → параметры

### Allure-отчёт локально

```bash
make report
```

---

## 6. Поддержка через AI (PyCharm + AI-агент)

Проект рассчитан на поддержку через AI-агента — написание нового кода вручную не требуется.

### Вариант 1: PyCharm + встроенный AI Assistant

PyCharm Professional имеет встроенный AI Assistant (JetBrains AI):

1. Settings → Plugins → убедиться что **AI Assistant** включён
2. Settings → Tools → AI Assistant → выбрать модель (рекомендуется Claude)
3. Открыть чат: View → Tool Windows → AI Assistant
4. В чате можно прикреплять файлы через `@` — агент увидит контекст

### Как работать с AI-агентом

**Тесты упали в CI:**
> "Посмотри последний прогон бекенд-тестов, вот лог ошибок: [вставить]. Почини"

**Изменился API:**
> "Эндпоинт CreateProject теперь принимает обязательное поле `icon`. Обнови эндпоинт и все тесты которые его используют"

**Новый тест:**
> "Напиши тест для эндпоинта RemoveAccessGroup. Используй стиль из test_custom_group.py. Фикстуры бери из conftest.py"

**Общие советы:**
- Всегда указывать файл-пример для стиля (например: "как в test_custom_group.py")
- Просить `pytest --collect-only` перед коммитом — проверка что импорты не сломались
- При сложных изменениях просить план сначала, потом реализацию
- Контекст проекта описан в `CLAUDE.md` — агент подхватит конвенции автоматически

### Ключевые файлы для контекста

При работе с агентом полезно прикрепить к чату:

| Что чинить | Какие файлы дать агенту |
|------------|------------------------|
| Backend-тесты | `tests/conftest.py` + conftest тестируемого модуля + файл теста |
| Эндпоинты | `tests/test_backend/data/endpoints/` — нужный модуль |
| Frontend-тесты | `tests/test_frontend/core/locators.py` + файл теста |
| CI | `.github/workflows/` — нужный workflow |
| Общие вопросы | `CLAUDE.md` + `docs/HANDOVER.md` |
