import json

from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout

from .models import Dish, Order, DishForOrder
from .forms import UserCreationForm, OrderConfirmationForm
from .tasks import send_order_confirmation_email



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
    def get(self, request):
        logout(request)
        return redirect('first')


def home(request):
    return render(request, "basis/home.html")


def detail(request, pizza_id):
    pizza = Dish.objects.get(id=pizza_id)  # Retrieve the pizza using its ID or another unique identifier
    return render(request, 'basis/detail.html', {'pizza': pizza})


def menu(request):
    pizzas = Dish.objects.all()
    return render(request, 'basis/menu.html', {'pizzas': pizzas})


def order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        open_order = Order.objects.get(user_id=request.user, status="Подтверждение заказа")
        order_id = open_order.id

        order_items = DishForOrder.objects.filter(order_id=order_id)
        dishes = Dish.objects.filter(id__in=[item.dish_id for item in order_items])

        confirmation_form = OrderConfirmationForm(request.POST or None)

        if request.method == 'POST' and confirmation_form.is_valid():
            confirm_order = confirmation_form.cleaned_data['confirm_order']

            if confirm_order:
                send_order_confirmation_email.delay(request.user.email, dishes)
                open_order.status = 'confirmed'
                open_order.save()

                return render(request, 'basis/order_confirmation.html')
            else:
                return redirect('order')

        return render(request, 'basis/order.html', {'dishes': dishes, 'confirmation_form': confirmation_form})
    except Order.DoesNotExist:
        return redirect('error')
    except Exception as e:
        print(f"Error getting order data: {e}")
        return redirect('error')


def error(request):
    return render(request, 'basis/error.html')


def add_to_order(request, pizza_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        # Проверка наличия открытого заказа для пользователя
        open_order = Order.objects.filter(user_id=request.user, status='Подтверждение заказа').first()

        if open_order:
            order = open_order
        else:
            # Создание нового заказа, если открытого заказа нет
            create_order = Order(user_id=request.user, courier=None, status='Подтверждение заказа')
            create_order.save()
            order = create_order

        order_id = order.id
    except Exception as e:
        print(f"Error creating/opening order: {e}")
        return redirect('error')

    try:
        # Создание записи о блюде для заказа
        create_dish_for_order = DishForOrder(order_id=order_id, dish_id=pizza_id)
        create_dish_for_order.save()
    except Exception as e:
        print(f"Error adding dish to order: {e}")
        return redirect('basis/error.html')

    return redirect('menu')


def confirm_order(request):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        open_order = Order.objects.filter(user_id=request.user, status='open').first()

        if open_order:
            open_order.status = 'confirmed'
            open_order.save()
    except Exception as e:
        print(f"Error confirming order: {e}")
        return redirect('basis/error.html')

    return redirect('basis/menu.html')
