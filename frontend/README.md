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
