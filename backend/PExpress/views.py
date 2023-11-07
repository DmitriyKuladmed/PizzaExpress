import json

from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout

from .models import Dish
from .forms import UserCreationForm


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


def menu(request):
    pizzas = Dish.objects.all()
    return render(request, 'basis/menu.html', {'pizzas': pizzas})


def order(request):
    pass

