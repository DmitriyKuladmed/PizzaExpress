from django import forms

from .models import Order, Dish, Ingredient, Menu

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('nickname', 'email')


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['courier', 'status']


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['id', 'pizza_name', 'price', 'weight', 'photo']


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['ingredient_name']


class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['menu_name']


class AddDishToOrderForm(forms.Form):
    dish = forms.ModelChoiceField(
        queryset=Dish.objects.all(),
        label="Select a dish to add",
        widget=forms.Select(attrs={'class': 'form-control'})
    )



