import json
import time

import requests

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Max, Sum
from django.db import transaction
from django.contrib.auth import login as auth_login, authenticate, logout
from django.views.decorators.csrf import csrf_exempt

from notifiers import get_notifier

from .models import Dish, Order, DishForOrder, Ingredient, TelegramUsers, User
from .forms import UserCreationForm, OrderConfirmationForm
from .tasks import send_order_confirmation_email
from .auth_data import token


def logger(message):
    with open('logs/app.log', 'a') as f:
        f.write(json.dumps(message) + '\n')


class Register(View):
    template_name = "registration/register.html"

    def get(self, request):
        try:
            context = {
                "form": UserCreationForm()
            }
            return render(request, self.template_name, context)

        except Exception as e:
            message = {
                'status': 400,
                'message': f"Во время регистрации произошла ошибка. {str(e)}"
            }
            logger(message)

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            nickname = form.cleaned_data.get('nickname')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            user = authenticate(nickname=nickname, email=email, password=password)
            auth_login(request, user)
            return redirect('first')
        else:
            return render(request, self.template_name, {
                'form': form
            })


class LogoutAndRedirect(View):
    @staticmethod
    def get(request):
        logout(request)
        return redirect('first')


def home(request):
    if request.user.is_authenticated:
        user_orders = []

        for order in Order.objects.filter(user_id=request.user):
            dish_names = get_dish_names_for_order(order.id)
            if dish_names:
                order.dish_names = dish_names
                user_orders.append(order)

        return render(request, 'basis/home.html', {'user_orders': user_orders, 'user': request.user})
    else:
        return render(request, 'basis/first_login.html')


def get_dish_names_for_order(order_id):
    try:
        dish_for_order_items = DishForOrder.objects.filter(order_id=order_id)
        dish_ids = [item.dish_id for item in dish_for_order_items]

        if dish_ids:
            dishes = Dish.objects.filter(id__in=dish_ids)
            return [dish.pizza_name for dish in dishes]
        else:
            return []
    except Exception as e:
        print(f"Error getting dish names for order: {e}")
        return []


def detail(request, pizza_id):
    pizza = Dish.objects.get(id=pizza_id)
    ingredients = Ingredient.objects.get(dish_id=pizza_id)
    print(ingredients)

    return render(request, 'basis/detail.html', {'pizza': pizza, 'ingredients': ingredients})


def menu(request):
    pizzas = Dish.objects.all()
    return render(request, 'basis/menu.html', {'pizzas': pizzas})


@transaction.atomic
def remove(request, order_id):
    user_id = None
    try:
        order_id = order_id
        order = Order.objects.get(id=order_id)
        order.status = 'Заказ выполнен✓'
        order.save()

        # Получаем пользователя с заказом в статусе "В процессе приготовления"
        user = User.objects.select_for_update().get(order__id=order_id, order__status="Заказ выполнен✓")

        # Получаем Telegram ID пользователя
        user_telegram_id = user.telegram_id

        # Получаем user_id из таблицы TelegramUsers по telegram_id
        try:
            telegram_user = TelegramUsers.objects.get(user_telegram=user_telegram_id)
            user_id = telegram_user.user_id
        except TelegramUsers.DoesNotExist:
            print(f'Пользователя с таким user_telegram_id не существует: {user_telegram_id}')

        # Отправляем уведомление
        success_mes = f'Статус заказа изменен на: "Заказ выполнен✓"\nПриятного аппетита :)'

        telegram = get_notifier('telegram')
        telegram.notify(token=token, chat_id=user_id, message=success_mes)

        return redirect('home')
    except Exception as e:
        print(f"Error removing pizzas: {e}")
        return JsonResponse({'success': False})


class OrderView(View):
    template_name = 'basis/order.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            max_order_id = Order.objects.filter(user_id=request.user).aggregate(Max('id'))['id__max']
            if max_order_id is not None:
                open_order = Order.objects.get(id=max_order_id, status="Подтверждение заказа")
                order_id = open_order.id
                order_items = DishForOrder.objects.filter(order_id=order_id)
                dishes = Dish.objects.filter(id__in=[item.dish_id for item in order_items])
                total_sum = dishes.aggregate(Sum('price'))['price__sum'] or 0
                pizza_list = []

                if open_order.promocode:
                    total_sum *= 0.5
                    for dish in dishes:
                        pizza_data = {
                            'id': dish.id,
                            'pizza_name': dish.pizza_name,
                            'photo_url': dish.photo.url,
                            'promo_price': dish.price * 0.5,
                            'weight': dish.weight,
                        }
                        pizza_list.append(pizza_data)

                    payment_form = OrderConfirmationForm()

                    return render(request, 'basis/order.html', {
                        'data_with_promo': {
                            'pizzas': pizza_list,
                            'order_id': order_id,
                            'total_sum': total_sum,
                        },
                        'payment_form': payment_form
                    })

                else:
                    payment_form = OrderConfirmationForm()

                    return render(request, self.template_name, {
                        'order_data': {'dishes': dishes,
                                       'order_id': order_id,
                                       'total_sum': total_sum
                                       },
                        'payment_form': payment_form
                    })
            else:
                return render(request, self.template_name, {
                    'order_data': None,
                    'payment_form': OrderConfirmationForm()
                })
        except Order.DoesNotExist:
            return redirect('error')
        except Exception as e:
            print(f"Error getting order data: {e}")
            return redirect('error')


class CreateOrderView(View):
    @staticmethod
    def post(request):
        if not request.user.is_authenticated:
            return redirect('login')

        url = "https://zvonok.com/manager/cabapi_external/api/v1/phones/call/"
        params = {
            "public_key": "25ac15841d365a56bc393cb5239e0483",
            "phone": request.user.phone,
            "campaign_id": "1057814085",
        }

        try:
            response = requests.get(url, params=params)
            print(response)
        except Exception as e:
            print(e)

        time.sleep(30)

        phone_number = request.user.phone
        campaign_id = "1057814085"
        public_key = "25ac15841d365a56bc393cb5239e0483"
        api_url = f"https://zvanok.by/manager/cabapi_external/api/v1/phones/calls_by_phone/?campaign_id={campaign_id}&phone={phone_number}&public_key={public_key}"

        try:
            max_order_id = Order.objects.filter(
                user_id=request.user,
                status="Подтверждение заказа"
            ).aggregate(Max('id'))['id__max']

            try:
                response = requests.get(api_url)
                calls_data = response.json()
                max_call_entry = max(
                    filter(lambda x: x["phone"] == phone_number, calls_data),
                    key=lambda x: x["call_id"]
                )

                # Check if ivr_data is a string and parse it if needed
                ivr_data = max_call_entry.get("ivr_data")
                if ivr_data:
                    if isinstance(ivr_data, str):
                        ivr_data = json.loads(ivr_data)

                    button_num = ivr_data[0].get("button_num")
                    if button_num is not None:
                        print(f"Button Number: {button_num}")
                    else:
                        print("Button Number not found in ivr_data")
                else:
                    print("ivr_data not present in the response")

            except Exception as e:
                print(f"Error fetching button_num: {e}")
                button_num = None

            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=max_order_id)
                order.status = "В процессе приготовления"
                order.save()

            Order.objects.create(id=max_order_id + 1, user_id=request.user, status="Подтверждение заказа")

            order_items = DishForOrder.objects.filter(order_id=max_order_id)
            dishes = Dish.objects.filter(id__in=[item.dish_id for item in order_items])
            dish_names = [dish.pizza_name for dish in dishes]

            payment_method = request.POST.get('payment_method')

            total_sum = request.POST.get('total_sum')
            print(total_sum)

            user = request.user
            user.promo = None
            user.save()
            send_order_confirmation_email.delay(request.user.telegram_id, request.user.email, dish_names,
                                                payment_method)

            return redirect('menu')
        except Order.DoesNotExist:
            return redirect('error')
        except Exception as e:
            print(f"Error creating order: {e}")
            return redirect('error')


@csrf_exempt
def call(request, number):
    if number == 1:
        return JsonResponse({"result": "1", "response_status": "200"})
    else:
        return JsonResponse({"result": "2", "response_status": "200"})


def error(request):
    return render(request, 'basis/error.html')


def add_promo(request):
    if request.method == 'POST':
        promo_code = request.POST.get('promo_code')
        user = request.user

        db_user = User.objects.get(nickname=user)

        max_order_id = Order.objects.filter(
            user_id=request.user
        ).aggregate(Max('id'))['id__max']

        order = Order.objects.get(id=max_order_id, user_id=db_user.id)

        open_order = Order.objects.get(id=max_order_id)
        order_id = open_order.id
        order_items = DishForOrder.objects.filter(order_id=order_id)
        dishes = Dish.objects.filter(id__in=[item.dish_id for item in order_items])
        total_sum = dishes.aggregate(Sum('price'))['price__sum'] or 0
        total_sum *= 0.5
        payment_form = OrderConfirmationForm()

        if promo_code == db_user.promo:
            db_user.total_promocodes += 1
            db_user.save()
            open_order.promocode = promo_code
            open_order.save()

            pizza_list = []
            for dish in dishes:
                pizza_data = {
                    'id': dish.id,
                    'pizza_name': dish.pizza_name,
                    'photo_url': dish.photo.url,
                    'promo_price': dish.price * 0.5,
                    'weight': dish.weight,
                }
                pizza_list.append(pizza_data)

            return render(request, 'basis/order.html', {
                'data_with_promo': {
                    'pizzas': pizza_list,
                    'order_id': order_id,
                    'total_sum': total_sum,
                },
                'payment_form': payment_form
            })
        else:
            pass

        return redirect("order")


def add_to_order(request, pizza_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        max_order_id = Order.objects.filter(user_id=request.user).aggregate(Max('id'))['id__max']

        open_order = Order.objects.filter(id=max_order_id, user_id=request.user, status='Подтверждение заказа').first()

        if open_order:
            order = open_order
        else:
            create_order = Order(user_id=request.user, courier=None, status='Подтверждение заказа')
            create_order.save()
            order = create_order

        order_id = order.id
    except Exception as e:
        print(f"Error creating/opening order: {e}")
        return redirect('error')

    try:
        create_dish_for_order = DishForOrder(order_id=order_id, dish_id=pizza_id)
        create_dish_for_order.save()
    except Exception as e:
        print(f"Error adding dish to order: {e}")
        return redirect('basis/error.html')

    return redirect('menu')
