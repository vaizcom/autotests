# VAIZ Autotests

## Preparing the project (Mac)
* Install [brew](https://brew.sh/)
* Install Python: `brew install python`
* Install dependencies: `pip install -r requirements.txt`
* Install allure: `brew install allure`
* Install playwright: `playwright install`

## Бекенд тесты

### Запуск в GitHub Actions
Бекенд тесты запускаются через воркфлоу **Backend Tests**.

**Ручной запуск:** Actions → Backend Tests → Run workflow → выбрать ветку, тесты и стенд.

Доступные стенды:
- `dev` — `https://api.vaiz.dev/v4`
- `kuber_dev` — `https://vaiz-api-ms.vaiz.dev/v4`
- `kuber_uat` — `https://vaiz-api-uat.vaiz.dev/v4`

Автозапуск: при пуше или PR в `main` по изменениям в `tests/test_backend/**`.

## Фронтенд тесты

### Запуск в GitHub Actions
Фронтенд тесты запускаются через воркфлоу **Frontend Tests**.

**Необходимые секреты** (Settings → Secrets and variables → Actions):
- `FRONTEND_EMAIL` — email тестового аккаунта на `app.vaiz.com`
- `FRONTEND_PASSWORD` — пароль тестового аккаунта

**Ручной запуск:** Actions → Frontend Tests → Run workflow → выбрать ветку и стенд.

Доступные стенды:
- `https://app.vaiz.com` (production) — работает сразу
- `https://app.vaiz.dev` (dev) — требует настройки VPN (см. ниже)

### Настройка VPN для dev стенда (для DevOps)
Чтобы фронтенд тесты работали на `https://app.vaiz.dev`, нужно добавить шаг в `frontend_tests.yml` перед шагом "Install Playwright browsers":

```yaml
- name: Setup VPN
  if: github.event.inputs.frontend_url == 'https://app.vaiz.dev'
  uses: Boostport/setup-cloudflare-warp@v1.6.0
  with:
    organization: vaiz
    auth_client_id: ${{ vars.CF_TOKEN_NAME }}
    auth_client_secret: ${{ secrets.CF_TOKEN }}
```

Необходимо:
- `CF_TOKEN_NAME` — variable (Settings → Secrets and variables → Variables)
- `CF_TOKEN` — secret (Settings → Secrets and variables → Actions)
- Раннер `ubuntu-latest-m` для dev стенда (уже прописан в воркфлоу)
