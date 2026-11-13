# Frontend

Клієнтська частина: HTML, CSS, JavaScript (ES-модулі), графіки — Chart.js.
Відповідальний: Frontend Developer.

Frontend **не** рахує ШКФ, не визначає ступінь анемії, не читає БД і не призначає
лікування. Він збирає дані, надсилає їх на сервер і показує відповідь.
Поля і маршрути — у [`docs/api-contract.md`](../docs/api-contract.md).

## Структура

```
frontend/
├── index.html                    # сторінка: форма, результат, історія
├── src/
│   ├── main.js                   # точка входу, з'єднує модулі
│   ├── config.js                 # адреса API
│   ├── api/                      # єдине місце, де є fetch
│   │   ├── httpClient.js         # запит, JSON, коди 201/422/500
│   │   ├── assessmentApi.js      # POST /api/assessments, історія
│   │   └── referenceApi.js       # GET /api/reference
│   ├── controllers/              # сценарії без DOM-деталей
│   │   ├── assessmentForm.js     # submitAssessment(view, api)
│   │   └── historyPage.js
│   ├── views/                    # робота з DOM
│   │   ├── assessmentFormView.js
│   │   ├── resultView.js
│   │   └── historyView.js
│   ├── components/               # повторно використовувані елементи
│   ├── validation/               # перевірки для зручності, не замість сервера
│   ├── charts/                   # Chart.js, без перерахунку формул
│   └── i18n/labels.js            # коди сервера -> українські підписи
├── styles/
├── assets/
└── tests/
```

## Напрямок залежностей

```
views / components  →  controllers  →  api  →  HTTP (Backend)
                                  ↘  validation, i18n
charts  ←  дані, які повернув api
```

`api/` нічого не знає про DOM, `views/` нічого не знає про fetch.
Контролер отримує API-клієнт параметром, тому в тестах його можна підмінити.

## Відповідність звіту Frontend

| Модуль у звіті | Тут |
| --- | --- |
| pages / views | `src/views/`, `index.html` |
| components | `src/components/` |
| api / assessmentApi.js | `src/api/` |
| validation | `src/validation/` |
| charts | `src/charts/` |
| обробник форми `submitAssessment` | `src/controllers/assessmentForm.js` |

## Реалізація та запуск

Інтерфейс реалізовано як адаптивний застосунок на HTML, CSS та JavaScript ES-модулях. Мобільний екран є основним; на мобільних пристроях доступна нижня навігація, на великих екранах — бічна. Chart.js використовується лише для відображення історії. Усі клінічні розрахунки та остаточна валідація залишаються на сервері.

```bash
cd frontend
npm install
npm run dev
```

За замовчуванням запити `/api/*` надсилаються на той самий origin. Якщо API працює окремо, задайте `VITE_API_BASE_URL` під час запуску Vite; сервер має дозволяти CORS для origin фронтенда. Маршрути та поля визначені в [`docs/api-contract.md`](../docs/api-contract.md). Без реалізованих серверних маршрутів форма показує повідомлення про помилку зв’язку; реальний результат і збережену історію вона не вигадує.

```bash
npm test
npm run build
```

Тести охоплюють клієнтську перевірку даних, формат запитів, успішне оцінювання, помилки 422 та мережеві збої. Для локальної перевірки інтерфейсу можна підмінити відповіді API в браузерному тесті відповідно до контракту.

## Акаунт і підключення до backend

Інтерфейс використовує серверну сесію з cookie `HttpOnly`; JavaScript не зберігає пароль або токен у `localStorage`. На старті клієнт викликає `GET /api/auth/session`. Реєстрація, вхід і вихід працюють через маршрути, описані у [BACKEND_INTEGRATION.md](BACKEND_INTEGRATION.md). Для перегляду іншого акаунта користувач виходить і входить з іншою поштою.

Без входу форма викликає лише `POST /api/assessments/preview`, який має повернути результат без запису в базу. Збереження через `POST /api/assessments` та історія доступні після входу. Приватна демоверсія підміняє API тестовими відповідями; реальні клінічні розрахунки в ній не виконуються. Модуль Chart.js завантажується лише під час відкриття історії.
