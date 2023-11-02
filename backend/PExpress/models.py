from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class User(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    nickname = models.CharField(max_length=25)
    tg_nickname = models.CharField(max_length=50)

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['id', 'nickname', 'tg_nickname']

    def get_nickname(self):
        return self.nickname


class Order(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    courier = models.CharField(max_length=60)
    status = models.CharField(max_length=60)

    def get_status(self):
        return self.status


class DishForOrder(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    dish_id = models.IntegerField


class Dish(models.Model):
    pizza_name = models.CharField(max_length=100)
    cooking_time = models.IntegerField
    gram = models.IntegerField
    photo = models.ImageField(verbose_name="Изображение", upload_to='media/', default='media/default.jpg')

    def get_pizza_name(self):
        return self.pizza_name


class DishElement(models.Model):
    dish_id = models.ForeignKey(Dish, on_delete=models.CASCADE)
    ingredient_id = models.IntegerField


class Ingredient(models):
    ingredient_name = models.CharField(max_length=60)

    def get_ingredient_name(self):
        return self.ingredient_name


class MenuElement(models.Model):
    dish_id = models.ForeignKey(Dish, on_delete=models.CASCADE)
    menu_id = models.IntegerField


class Menu(models.Model):
    menu_name = models.CharField(max_length=100)

    def get_menu_name(self):
        return self.menu_name


