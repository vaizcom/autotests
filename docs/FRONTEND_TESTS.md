# Frontend Tests — Руководство по запуску

## Требования

### GitHub Secrets

Перед первым запуском добавить в репозитории **Settings → Secrets and variables → Actions**:

| Secret | Описание | Пример |
|--------|----------|--------|
| `FRONTEND_EMAIL` | Email тестового пользователя | `test+auto@vaiz.com` |
| `FRONTEND_PASSWORD` | Пароль тестового пользователя | `123456` |

> Стенд — всегда прод: `https://app.vaiz.com`

---

## Запуск

### Автоматически

Воркфлоу **Frontend Tests** запускается автоматически при push или PR в `main`,
если изменены файлы в `tests/test_frontend/**`.

Бэковые тесты при этом **не запускаются**.

### Вручную

1. Перейти в репозиторий → вкладка **Actions**
2. Выбрать воркфлоу **Frontend Tests**
3. Нажать **Run workflow**
4. Выбрать ветку → **Run workflow**

---

## Отчёт

После прогона Allure Report публикуется на GitHub Pages:

```
https://vaizcom.github.io/autotests/
```

При открытии PR ссылка на отчёт появляется автоматически в комментарии.

---

## Локальный запуск

```bash
# Headless (как в CI)
pytest -m frontend

# С открытым браузером
pytest -m frontend --headed

# С замедлением (удобно для отладки)
pytest -m frontend --headed --slowmo 1000
```

Переменные окружения можно задать в `.env` файле в корне проекта:

```env
FRONTEND_EMAIL=test+auto@vaiz.com
FRONTEND_PASSWORD=123456
FRONTEND_URL=https://app.vaiz.com
```
