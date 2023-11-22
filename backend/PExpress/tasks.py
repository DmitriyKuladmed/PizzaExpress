import random
import requests

from django.db import transaction
from django.core.mail import send_mail

from notifiers import get_notifier

from backend.celery import app

from .models import Order, TelegramUsers, Promo, User
from .auth_data import token


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


@app.task(queue='email_queue')
def send_order_confirmation_email(user_telegram, user_email, order_details, payment_method):
    if payment_method == "cash":
        payment_method = "Наличными курьеру"
    else:
        payment_method = "Картой"
    order_details_str = ", ".join(order_details)
    confirmation_message = f"Ваш заказ с пиццами: {', '.join(order_details)}, со способом оплаты - {payment_method}, подтвержден!\n" \
                           f"Статус заказа: В процессе приготовления"

    subject = 'Вы сделали заказ в PizzaExpress!'
    plain_message = f"Спасибо за ваш заказ!\n\nДетали вашего заказа:\n{order_details_str}\n\nСпособ оплаты: {payment_method}"
    from_email = 'dima.kulaga5@gmail.com'
    send_mail(subject, plain_message, from_email, [user_email])

    user = TelegramUsers.objects.get(user_telegram=user_telegram)
    chat_with_user_id = user.user_id
    telegram = get_notifier('telegram')
    telegram.notify(token=token, chat_id=user.user_id, message=confirmation_message)

    interval_seconds = random.randint(15, 25)
    give_promo.apply_async((user_telegram, chat_with_user_id,), countdown=interval_seconds)


@app.task(queue='promo_queue')
def give_promo(user_telegram, chat_with_user_id):
    user = User.objects.get(telegram_id=user_telegram)

    if not user.promo:
        random_promo = Promo.objects.order_by('?').first()

        user.promo = random_promo.promo_name
        user.save()
        success_mes = f"Вам выдан промокод {user.promo} на второй заказ!\n" \
                      f"Введите его при следующем заказе и получите 50% скидки!\n"

        telegram = get_notifier('telegram')
        telegram.notify(token=token, chat_id=chat_with_user_id, message=success_mes)

        print(success_mes)
    else:
        print(f"Пользователь {user_telegram} уже имеет промокод")


@app.task(queue='processing_status_queue')
def update_order_status():
    try:
        orders = Order.objects.filter(status="В процессе приготовления")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(20, 25)

                update_order_status_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task(queue='processing_status_queue')
def update_order_status_delayed(order_id):
    try:
        with transaction.atomic():
            # Получаем пользователя с заказом в статусе "В процессе приготовления"
            user = User.objects.select_for_update().get(order__id=order_id, order__status="В процессе приготовления")

            # Получаем Telegram ID пользователя
            user_telegram_id = user.telegram_id

            # Получаем user_id из таблицы TelegramUsers по telegram_id
            try:
                telegram_user = TelegramUsers.objects.get(user_telegram=user_telegram_id)
                user_id = telegram_user.user_id
            except TelegramUsers.DoesNotExist:
                print(f'Пользователя с таким user_telegram_id не существует: {user_telegram_id}')

            # Обновляем статус заказа
            Order.objects.filter(id=order_id).update(status="Поиск курьера для доставки")

            # Отправляем уведомление
            success_mes = f'Статус заказа изменен на: "Поиск курьера для доставки"'
            telegram = get_notifier('telegram')
            telegram.notify(token=token, chat_id=user_id, message=success_mes)

            print(success_mes)

    except User.DoesNotExist:
        print(f'User with order {order_id} not found or not in "В процессе приготовления" status')
    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task(queue='courier_status_queue', max_retries=1)
def assign_courier_and_update_status():
    try:
        orders = Order.objects.filter(status="Поиск курьера для доставки")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(20, 25)

                update_order_status_on_success_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task(queue='courier_status_queue', max_retries=1)
def update_order_status_on_success_delayed(order_id):
    try:
        with transaction.atomic():
            # Получаем заказ
            order = Order.objects.get(id=order_id)

            # Выбираем случайного курьера (предполагается, что у вас есть список `couriers`)
            random_courier = random.choice(couriers)

            # Обновляем данные заказа
            order.courier = random_courier
            order.status = "Ваш заказ доставляется"
            order.save()

            # Получаем пользователя с заказом в статусе "В процессе приготовления"
            user = User.objects.get(order__id=order_id, order__status="Ваш заказ доставляется")

            # Получаем Telegram ID пользователя
            user_telegram_id = user.telegram_id

            # Получаем user_id из таблицы TelegramUsers по telegram_id
            try:
                telegram_user = TelegramUsers.objects.get(user_telegram=user_telegram_id)
                user_id = telegram_user.user_id
            except TelegramUsers.DoesNotExist:
                print(f'Пользователя с таким user_telegram_id не существует: {user_telegram_id}')

            # Отправляем уведомление
            success_mes = f'Статус заказа изменен на: "Ваш заказ доставляется"\nВаш курьер: {random_courier}.'

            telegram = get_notifier('telegram')
            telegram.notify(token=token, chat_id=user_id, message=success_mes)

            print(success_mes)

    except Order.DoesNotExist:
        print(f'Order {order_id} not found')
    except Exception as e:
        print(f'Error updating order status: {e}')


@app.task(queue='expectation_status_queue', max_retries=1)
def update_order_status_on_delivery():
    try:
        orders = Order.objects.filter(status="Ваш заказ доставляется")

        with transaction.atomic():
            for order in orders:
                interval_seconds = random.randint(20, 25)

                update_order_status_on_delivery_delayed.apply_async((order.id,), countdown=interval_seconds)

    except Exception as e:
        print(f'Error updating order status on delivery: {e}')


@app.task(queue='expectation_status_queue', max_retries=1)
def update_order_status_on_delivery_delayed(order_id):
    try:
        with transaction.atomic():
            order = Order.objects.get(id=order_id)
            order.status = "Курьер на месте!"
            order.save()

            # Получаем пользователя с заказом в статусе "В процессе приготовления"
            user = User.objects.get(order__id=order_id, order__status="Курьер на месте!")

            # Получаем Telegram ID пользователя
            user_telegram_id = user.telegram_id

            # Получаем user_id из таблицы TelegramUsers по telegram_id
            try:
                telegram_user = TelegramUsers.objects.get(user_telegram=user_telegram_id)
                user_id = telegram_user.user_id
            except TelegramUsers.DoesNotExist:
                print(f'Пользователя с таким user_telegram_id не существует: {user_telegram_id}')

            success_mes = f'Статус заказа изменен на: "Курьер на месте!"\nЗаберите заказ!'

            telegram = get_notifier('telegram')
            telegram.notify(token=token, chat_id=user_id, message=success_mes)

            print(success_mes)

    except Order.DoesNotExist:
        print(f'Order {order_id} not found')
    except Exception as e:
        print(f'Error updating order status on delivery: {e}')
