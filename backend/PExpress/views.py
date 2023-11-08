import json

from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout

from .models import Dish, Order, DishForOrder
from .forms import UserCreationForm, AddDishToOrderForm


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
            tg_nickname = form.cleaned_data.get('tg_nickname')
            password = form.cleaned_data.get('password1')
            user = authenticate(nickname=nickname, tg_nickname=tg_nickname, password=password)
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
    pass


def add_to_order(request, order_id):
    if not request.user.is_authenticated:
        return redirect('login')

    try:
        order = Order.objects.get(id=order_id, user_id=request.user)
    except Order.DoesNotExist:

        return redirect('menu')

    if request.method == 'POST':
        form = AddDishToOrderForm(request.POST)
        if form.is_valid():
            dish_id = form.cleaned_data['dish']
            dish = Dish.objects.get(id=dish_id)

            dish_for_order = DishForOrder(order_id=order, dish_id=dish)
            dish_for_order.save()

            return redirect('menu', order_id=order_id)
    else:
        form = AddDishToOrderForm()

    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'basis/menu.html', context)

