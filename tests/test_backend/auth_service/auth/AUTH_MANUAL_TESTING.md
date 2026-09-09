# Ручное тестирование нового флоу авторизации (Postman)

Base URL: `https://api.vaiz.dev/v4`

---

## Логин (существующий пользователь)

### Шаг 1: AuthWithEmail

```
POST {{base_url}}/AuthWithEmail
Content-Type: application/json

{
  "email": "your_email@gmail.com"
}
```

**Ответ (200):**
```json
{
  "payload": {
    "needPassword": true,
    "tempToken": "eyJhbGciOiJIUz..."
  },
  "type": "AuthWithEmail"
}
```

`needPassword: true` означает, что email найден в базе — это логин.

Скопировать `tempToken` из ответа.

### Шаг 2: VerifyPassword

```
POST {{base_url}}/VerifyPassword
Content-Type: application/json

{
  "tempToken": "eyJhbGciOiJIUz...",
  "password": "your_password"
}
```

**Ответ (200):**
```json
{
  "payload": {
    "authToken": "eyJhbGciOiJIUz...",
    "newUser": false
  },
  "type": "VerifyPassword"
}
```

`authToken` — токен авторизации для дальнейших запросов.
`newUser: false` — пользователь уже существовал.

---

## Регистрация (новый пользователь)

### Шаг 1: AuthWithEmail

```
POST {{base_url}}/AuthWithEmail
Content-Type: application/json

{
  "email": "new_email@gmail.com"
}
```

**Ответ (200):**
```json
{
  "payload": {
    "needPassword": false,
    "tempToken": "eyJhbGciOiJIUz...",
    "needOTP": true
  },
  "type": "AuthWithEmail"
}
```

`needOTP: true` означает, что email не найден в базе — это регистрация. На почту отправлен OTP-код.

Скопировать `tempToken` из ответа.

### Шаг 2: Получить OTP-код

**Вариант А — из почты:** проверить входящие письма на указанном email.

**Вариант Б — из MongoDB** (если нет доступа к почте):

1. Скопировать `tempToken` из ответа шага 1
2. Открыть https://jwt.io/ (см. инструкцию ниже)
3. Вставить `tempToken` в поле "Encoded"
4. В разделе "Decoded → PAYLOAD" найти поле `id`
5. В MongoDB выполнить запрос:
   ```
   db.confirmtokens.findOne({ _id: ObjectId("значение_id_из_jwt") })
   ```
6. OTP-код находится в поле `payload.otpCode`

### Шаг 3: VerifyOtp

```
POST {{base_url}}/VerifyOtp
Content-Type: application/json

{
  "tempToken": "eyJhbGciOiJIUz...",
  "otp": "123456"
}
```

**Ответ (200):**
```json
{
  "payload": {
    "authToken": "eyJhbGciOiJIUz...",
    "newUser": true
  },
  "type": "VerifyOtp"
}
```

`newUser: true` — новый пользователь зарегистрирован.

---

## Как декодировать JWT на jwt.io

1. Открыть https://jwt.io/
2. В левой части ("Encoded") вставить токен (tempToken или authToken)
3. В правой части ("Decoded") автоматически появятся три секции:
   - **HEADER** — алгоритм и тип токена
   - **PAYLOAD** — данные токена:
     - `email` — email пользователя
     - `flow` — тип флоу (login / register)
     - `step` — текущий шаг
     - `id` — ID записи в коллекции `confirmtokens` (MongoDB)
     - `iat` — время создания (Unix timestamp)
     - `exp` — время истечения (Unix timestamp, +10 минут от iat)
   - **VERIFY SIGNATURE** — подпись (для проверки не нужна)

> Подпись не валидируется без серверного секрета — это нормально, jwt.io покажет "Invalid Signature". Для просмотра данных это не важно.

---

## Важно

- `tempToken` — одноразовый. После успешного VerifyPassword/VerifyOtp он удаляется из базы
- `tempToken` живет 10 минут (поле `exp` в JWT)
- Токен от логина (needPassword) нельзя использовать в VerifyOtp и наоборот
- `authToken` нельзя использовать вместо `tempToken`

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| `InvalidEmail` | Некорректный формат email |
| `WrongCredentials` | Неверный пароль |
| `FieldCantBeBlanc` | Пустое обязательное поле |
| `OTPCodeNotValid` | Неверный OTP-код |
| `JwtIncorrect` | Мусорный/невалидный токен |
| `JwtDoesNotExits` | Токен не найден в базе (использован или истек) |
| `InvalidForm` | Общая ошибка валидации формы |

Структура ошибки:
```json
{
  "payload": null,
  "type": "VerifyPassword",
  "error": {
    "code": "InvalidForm",
    "originalType": "VerifyPassword",
    "fields": [
      {
        "name": "password",
        "codes": ["WrongCredentials"]
      }
    ]
  }
}
```
