from django import forms

from .models import Order

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('nickname', 'tg_nickname')


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['courier', 'status']

