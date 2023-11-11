import backend

from django.urls import path, include
from rest_framework import routers
from django.conf.urls.static import static

from . import views


router = routers.SimpleRouter()


urlpatterns = [
    path("", include("django.contrib.auth.urls")),
    path("register/", views.Register.as_view(), name="register"),
    path("home/", views.home, name="home"),
    path("menu/", views.menu, name="menu"),
    path("error/", views.error, name="error"),
    path("menu/detail/<int:pizza_id>/", views.detail, name="detail"),
    path('order/', views.OrderView.as_view(), name='order'),
    path('remove_pizzas/<int:order_id>/', views.remove, name="remove"),
    path('create_order/', views.CreateOrderView.as_view(), name='create_order'),
    path("add_to_order/<int:pizza_id>/", views.add_to_order, name="add_to_order"),
    path('logout-and-redirect/', views.LogoutAndRedirect.as_view(), name='logout_and_redirect'),

]

if backend.settings.DEBUG:
    urlpatterns += static(backend.settings.MEDIA_URL, document_root=backend.settings.MEDIA_ROOT)
