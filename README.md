# DonerCraft Backend Demo (Django + SQLite)

Это минимальный backend + БД под учебный проект:
- конструктор (правила/пересчет цены на сервере)
- корзина (session-based)
- оформление заказа
- статусы заказа (в админке)
- промокоды (пример DONER10)
- демо-оплата (simulate-paid)

## Быстрый старт

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Открой:
- http://127.0.0.1:8000/ (лендинг)
- http://127.0.0.1:8000/builder/ (пример конструктора)
- http://127.0.0.1:8000/cart/
- http://127.0.0.1:8000/checkout/
- http://127.0.0.1:8000/admin/

## Где "вставлять Django" в твоем фронте
- Данные (размеры/основа/ингредиенты): `GET /api/builder/options/`
- Пересчет цены: `POST /api/builder/calculate/`
- Добавить в корзину: `POST /api/cart/add/`
- Корзина: `GET /api/cart/`
- Оформление: `POST /api/checkout/`
