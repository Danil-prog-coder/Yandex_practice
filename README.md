# Booking Service

HTTP-сервис для управления бронированиями мест. Хранит данные в PostgreSQL,
написан на FastAPI.

## Запуск

```bash
pip install -r requirements.txt
python main.py --port 8080
```

Сервис поднимется на `http://127.0.0.1:8080`.

## Подключение к базе

Параметры берутся из переменных окружения (значения по умолчанию в скобках):

| Переменная    | По умолчанию |
|---------------|--------------|
| `DB_HOST`     | `localhost`  |
| `DB_PORT`     | `5432`       |
| `DB_USER`     | `postgres`   |
| `DB_PASSWORD` | `postgres`   |
| `DB_NAME`     | `contest`    |

Ожидается таблица:

```sql
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    place_id INTEGER NOT NULL,
    time_from TIMESTAMP NOT NULL,
    time_to TIMESTAMP NOT NULL
);
```

## API

### `GET /ping`
Health check. Возвращает `200` и `{"status":"ok"}`.

### `POST /book`
Создаёт бронирование. Query-параметры: `place_id`, `user_id`, `from`, `to`
(время в формате RFC3339, например `2024-01-01T10:00:00Z`).

- `200` — бронирование создано;
- `409` — интервал пересекается с уже существующим бронированием места.

Интервалы считаются полуоткрытыми `[from, to)`: пересечение есть, если
`time_from < new_to AND new_from < time_to`.

### `GET /booklist`
Список бронирований по одному из фильтров: `user_id` или `place_id`.
Результат отсортирован по `(from, id)` по возрастанию.

```json
{
  "bookings": [
    {
      "id": 1,
      "user_id": 10,
      "place_id": 5,
      "from": "2024-01-01T10:00:00Z",
      "to": "2024-01-01T12:00:00Z"
    }
  ]
}
```

## Структура

- `main.py` — приложение целиком: подключение к БД, разбор времени и три эндпоинта.
- `requirements.txt` — зависимости (FastAPI, uvicorn, psycopg2).

## Особенности реализации

- Время хранится как наивный UTC, на выходе всегда отдаётся с суффиксом `Z`.
- Сервер запускается в один процесс (`workers=1`) — рассчитан на
  последовательные блокирующие запросы.
