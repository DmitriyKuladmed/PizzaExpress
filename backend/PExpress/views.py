import json

from django.http import JsonResponse
from django.views import View
from django.shortcuts import render, redirect
from django.db.models import Max
from django.db import transaction
from django.contrib.auth import login as auth_login, authenticate, logout

from .models import Dish, Order, DishForOrder, Ingredient
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


def remove(request, order_id):
    try:
        order_id = order_id
        order = Order.objects.get(id=order_id)
        order.status = 'Заказ выполнен✓'
        order.save()

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

                payment_form = OrderConfirmationForm()

                return render(request, self.template_name, {
                    'order_data': {'dishes': dishes, 'order_id': order_id},
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

        try:
            max_order_id = Order.objects.filter(
                user_id=request.user,
                status="Подтверждение заказа"
            ).aggregate(Max('id'))['id__max']

            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=max_order_id)
                order.status = "В процессе приготовления"
                order.save()

            Order.objects.create(user_id=request.user, status="Подтверждение заказа")

            order_items = DishForOrder.objects.filter(order_id=max_order_id)
            dishes = Dish.objects.filter(id__in=[item.dish_id for item in order_items])
            dish_names = [dish.pizza_name for dish in dishes]

            payment_method = request.POST.get('payment_method')

            # Send confirmation email
            send_order_confirmation_email.delay(request.user.email, dish_names, payment_method)

            return redirect('menu')
        except Order.DoesNotExist:
            return redirect('error')
        except Exception as e:
            print(f"Error creating order: {e}")
            return redirect('error')


def error(request):
    return render(request, 'basis/error.html')


def add_to_order(request, pizza_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        # Get the user's maximum order id
        max_order_id = Order.objects.filter(user_id=request.user).aggregate(Max('id'))['id__max']

        # Check if there is an open order for the user
        open_order = Order.objects.filter(id=max_order_id, user_id=request.user, status='Подтверждение заказа').first()

        if open_order:
            order = open_order
        else:
            # Create a new order if there is no open order
            create_order = Order(user_id=request.user, courier=None, status='Подтверждение заказа')
            create_order.save()
            order = create_order

        order_id = order.id
        print(order_id)
    except Exception as e:
        print(f"Error creating/opening order: {e}")
        return redirect('error')

    try:
        # Create a record for the pizza in the order
        create_dish_for_order = DishForOrder(order_id=order_id, dish_id=pizza_id)
        create_dish_for_order.save()
    except Exception as e:
        print(f"Error adding dish to order: {e}")
        return redirect('basis/error.html')

    return redirect('menu')
