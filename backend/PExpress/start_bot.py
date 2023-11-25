import os
import sys
import django
import telebot
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

sys.path.append("C:\\Users\\dimak\\PycharmProjects\\pizzaExpress\\backend")
print(sys.path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from PExpress.models import TelegramUsers
from PExpress.auth_data import token, url

bot = telebot.TeleBot(token)
welcome_message = (
    "Привет! Это PizzaExpress Bot.\n"
    "Я буду присылать тебе статус твоего заказа, как только он будет меняться!\n"
)


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id
    print(chat_id)
    bot.send_message(chat_id, welcome_message)
    new_user, created = TelegramUsers.objects.get_or_create(user_id=chat_id)

    if created:
        print(f"Новый пользователь добавлен: {chat_id}")
    else:
        print(f"Пользователь уже есть в базе данных: {chat_id}")


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        json_str = request.body.decode('UTF-8')
        update = Update.de_json(json.loads(json_str))
        bot.process_new_updates([update])
        return HttpResponse('')
    else:
        return HttpResponse('This endpoint is meant for Telegram webhook, use POST request.', status=405)


bot.infinity_polling(skip_pending=True)
