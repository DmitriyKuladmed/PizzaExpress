import random

from django.db import transaction
from django.core.mail import send_mail

from backend.celery import app

from .models import Order



couriers = [
    "Алексей Дмитровской",
    "Дмитрий Донской",
    "Владимир Орехов",
    "Андрей Никольский",
    "Кирилл Остапенко",
    "Даниил Остапук",
    "Игорь Маркевич",
    "Владислав Чесняк",
    "Василий Кидук",
    "Никита Вахиленко",
]


@app.task
def send_order_confirmation_email(user_email, order_details, payment_method):
    if payment_method == "cash":
        payment_method = "Наличными курьеру"
    else:
        payment_method = "Картой"
    order_details_str = ", ".join(order_details)

    subject = 'Вы сделали заказ в PizzaExpress!'
    plain_message = f"Спасибо за ваш заказ!\n\nДетали вашего заказа:\n{order_details_str}\n\nСпособ оплаты: {payment_method}"
    from_email = 'dima.kulaga5@gmail.com'
    send_mail(subject, plain_message, from_email, [user_email])


@app.task
def update_order_status():
    try:
        orders = Order.objects.filter(status="В процессе приготовления")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(40, 60)

                update_order_status_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task
def update_order_status_delayed(order_id):
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            order.status = "Поиск курьера для доставки"
            order.save()

        print(f'Order {order_id} status updated to "Поиск курьера для доставки"')

    except Order.DoesNotExist:
        print(f'Order {order_id} not found')
    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task
def assign_courier_and_update_status():
    try:
        orders = Order.objects.filter(status="Поиск курьера для доставки")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(40, 60)

                update_order_status_on_success_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task
def update_order_status_on_success_delayed(order_id):
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            random_courier = random.choice(couriers)

            order.courier = random_courier
            order.status = "Ваш заказ доставляется"
            order.save()

        print(f'Order {order_id} status updated to "Поиск курьера для доставки"')

    except Order.DoesNotExist:
        print(f'Order {order_id} not found')
    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task
def update_order_status_on_delivery():
    try:
        orders = Order.objects.filter(status="Ваш заказ доставляется")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(40, 60)

                update_order_status_on_delivery_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status on delivery: {e}')


@app.task
def update_order_status_on_delivery_delayed(order_id):
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            order.status = "Курьер на месте!"
            order.save()

        print(f'Order {order_id} status updated to "Курьер на месте!"')

    except Order.DoesNotExist:
        print(f'Order {order_id} not found')
    except Exception as e:
        print(f'Error updating order status on delivery: {e}')
