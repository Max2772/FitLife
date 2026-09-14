"""
Выгрузка всех страниц сайта в HTML для проверки валидатором W3C.

    python scripts/dump_pages.py

Скрипт обходит публичные адреса, проверяет код ответа 200 и сохраняет готовую
разметку в каталог rendered/. Дополнительно проигрывает сценарий покупки:
добавление в корзину -> изменение количества -> оформление -> оплата.
"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LB5.settings')
os.environ.setdefault('LOG_LEVEL', 'ERROR')
django.setup()

import logging
logging.disable(logging.CRITICAL)

from django.test import Client as TestClient
from django.contrib.auth.models import User
from gym.models import MembershipType, Article, Trainer

OUT = os.path.join(BASE_DIR, 'rendered')
os.makedirs(OUT, exist_ok=True)

membership = MembershipType.objects.order_by('id').first()
article = Article.objects.order_by('id').first()
trainer = Trainer.objects.order_by('id').first()

PAGES = [
    ('main', '/'),
    ('catalog', '/catalog/'),
    ('product_detail', f'/catalog/{membership.pk}/'),
    ('cart', '/cart/'),
    ('about', '/about/'),
    ('contacts', '/contacts/'),
    ('faq', '/faq/'),
    ('news', '/news/'),
    ('news_detail', f'/news/{article.pk}/'),
    ('privacy', '/privacy/'),
    ('vacancies', '/vacancies/'),
    ('promocodes', '/promocodes/'),
    ('reviews', '/reviews/'),
    ('trainings', '/trainings/'),
    ('trainers', '/trainers/'),
    ('trainer_detail', f'/trainers/{trainer.pk}/'),
    ('halls', '/halls/'),
    ('equipment', '/equipment/'),
    ('memberships', '/memberships/'),
    ('login', '/login/'),
    ('register', '/register/'),
]

client = TestClient()
failures = []

for name, url in PAGES:
    try:
        response = client.get(url, follow=True)
    except Exception as exc:  # noqa: BLE001
        failures.append((name, url, f"EXCEPTION: {exc}"))
        continue
    if response.status_code != 200:
        failures.append((name, url, f"HTTP {response.status_code}"))
        continue
    with open(os.path.join(OUT, f"{name}.html"), 'wb') as fh:
        fh.write(response.content)
    print(f"OK  {response.status_code}  {url}")

# --- сценарий корзины -----------------------------------------------------
print("\n--- сценарий корзины ---")
response = client.post(f'/cart/add/{membership.pk}/', {'quantity': 2, 'next': 'cart'}, follow=True)
print("add ->", response.status_code, response.request['PATH_INFO'])

cart_page = client.get('/cart/')
open(os.path.join(OUT, 'cart_filled.html'), 'wb').write(cart_page.content)
print("cart ->", cart_page.status_code)

checkout_page = client.get('/checkout/', follow=True)
open(os.path.join(OUT, 'checkout.html'), 'wb').write(checkout_page.content)
print("checkout ->", checkout_page.status_code)

pay = client.post('/checkout/', {
    'full_name': 'Иванов Иван',
    'email': 'ivanov@example.by',
    'phone': '+375 29 123-45-67',
    'start_date': '2026-10-01',
    'payment_method': 'card',
    'card_number': '4111 1111 1111 1111',
    'promocode': '',
    'comment': 'Тестовая оплата',
    'agree': 'on',
}, follow=True)
print("pay ->", pay.status_code, pay.request['PATH_INFO'])
if pay.status_code == 200 and '/order/' in pay.request['PATH_INFO']:
    open(os.path.join(OUT, 'order_success.html'), 'wb').write(pay.content)
else:
    failures.append(('checkout POST', '/checkout/', f"не создан заказ: {pay.request['PATH_INFO']}"))
    body = pay.content.decode('utf-8', 'replace')
    import re
    for err in re.findall(r'<p class="text-danger small">(.*?)</p>', body):
        print("   ошибка формы:", err)

# --- сценарий формы обратной связи ---------------------------------------
print("\n--- форма обратной связи ---")
feedback = client.post('/contacts/', {
    'full_name': 'Пётр',
    'email': 'petr@example.by',
    'phone': '+375 33 765-43-21',
    'age': 30,
    'topic': 'personal',
    'department': 'reception',
    'channels': ['email'],
    'satisfaction': 9,
    'label_color': '#ff6b00',
    'message': 'Подскажите, есть ли утренние групповые занятия по йоге?',
    'agree': 'on',
}, follow=True)
print("feedback ->", feedback.status_code)

print()
if failures:
    print("!!! ПРОБЛЕМЫ:")
    for name, url, reason in failures:
        print(f"  {name} ({url}): {reason}")
    sys.exit(1)
print("Все страницы отрендерены без ошибок.")
