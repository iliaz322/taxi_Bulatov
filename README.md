# Taxi Project

Полноценный учебный сайт для заказа такси на Django.

## Стек

- Backend — Django 4.x
- Database — SQLite для разработки / PostgreSQL для продакшена
- Frontend — HTML, CSS, vanilla JavaScript
- Auth — `django.contrib.auth`
- Admin — Django admin

## Структура

- `taxi_project/` — настройки проекта и маршруты
- `users/` — кастомный пользователь, регистрация, вход, профиль
- `rides/` — тарифы, поездки, история, отзывы, mock-водители
- `static/` — стили и JavaScript

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata rides/fixtures/tariffs.json
python manage.py createsuperuser
python manage.py runserver
```

## Начальные данные

Загрузить тарифы:

```bash
python manage.py loaddata rides/fixtures/tariffs.json
```

## Переменные окружения

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Если переменные PostgreSQL не заданы, используется SQLite.

## Маршруты

- `/` — лендинг
- `/order/` — заказ поездки
- `/ride/<id>/` — статус поездки
- `/ride/<id>/rate/` — оценка поездки
- `/history/` — история поездок
- `/accounts/login/` — вход
- `/accounts/logout/` — выход
- `/accounts/register/` — регистрация
- `/accounts/profile/` — профиль
- `/admin/` — админка
