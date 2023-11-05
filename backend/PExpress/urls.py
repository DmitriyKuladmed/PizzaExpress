from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()


urlpatterns = [
    path("register/", views.Register.as_view(), name="register"),
]
