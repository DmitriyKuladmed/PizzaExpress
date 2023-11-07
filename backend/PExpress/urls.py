from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()


urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("register/", views.Register.as_view(), name="register"),
    path('logout-and-redirect/', views.LogoutAndRedirect.as_view(), name='logout_and_redirect'),
    path("home/", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("order/", views.order, name="order"),
]
