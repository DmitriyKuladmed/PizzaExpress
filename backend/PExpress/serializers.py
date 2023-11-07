from rest_framework import viewsets, serializers

from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class OrderForm(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['courier', 'status']


class DishForm(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['pizza_name', 'price', 'weight', 'photo']


class IngredientForm(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['ingredient_name']


class MenuForm(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['menu_name']

