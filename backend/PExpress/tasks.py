from celery import Celery
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from backend.celery import app


@app.task
def send_order_confirmation_email(user_email, order_details, payment_method):
    subject = 'Вы сделали заказ в PizzaExpress!'
    plain_message = f"Спасибо за ваш заказ!\n\nДетали вашего заказа:\n{order_details}\n\nPayment Method: {payment_method}"
    from_email = 'dima.kulaga5@gmail.com'
    send_mail(subject, plain_message, from_email, [user_email])