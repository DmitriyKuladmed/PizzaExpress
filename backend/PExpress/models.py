from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserAccountManager(BaseUserManager):
    def create_user(self, nickname, email, password=None):

        user = self.model(
            nickname=nickname,
            email=email,
        )

        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, nickname, email, password=None):
        user = self.create_user(
            nickname,
            email,
            password=password
        )

        user.is_staff = True
        user.is_superuser = True
        user.save()

        return user


class User(AbstractBaseUser):
    id = models.BigAutoField(primary_key=True)
    nickname = models.CharField(max_length=25, unique=True)
    email = models.CharField(max_length=50, null=True)
    promo = models.CharField(max_length=6, null=True)
    telegram_id = models.CharField(max_length=50, null=True)
    phone = models.CharField(max_length=15, null=True)

    objects = UserAccountManager()

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['email']

    def get_nickname(self):
        return self.nickname


class Order(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    courier = models.CharField(max_length=60, default=None, null=True)
    status = models.CharField(max_length=60, default="Подтвердите заказ")

    def get_status(self):
        return self.status


class Promo(models.Model):
    promo_name = models.CharField(max_length=6)


class TelegramUsers(models.Model):
    user_id = models.CharField(max_length=100)
    user_telegram = models.CharField(max_length=50, null=True)


class Dish(models.Model):
    id = models.AutoField(primary_key=True)
    pizza_name = models.CharField(max_length=100)
    price = models.CharField(max_length=20)
    weight = models.CharField(max_length=20)
    photo = models.ImageField(verbose_name="Изображение", upload_to='images/', default='images/default.jpg')

    def get_pizza_name(self):
        return self.pizza_name


class DishForOrder(models.Model):
    order_id = models.IntegerField(default=0)
    dish_id = models.IntegerField(default=0)


class Ingredient(models.Model):
    dish_id = models.IntegerField(default=0)
    ingredient_name = models.CharField(max_length=60)

    def get_ingredient_name(self):
        return self.ingredient_name


class DishElement(models.Model):
    dish_id = models.IntegerField(default=0)
    ingredient_id = models.IntegerField(default=0)


class Menu(models.Model):
    menu_name = models.CharField(max_length=100)

    def get_menu_name(self):
        return self.menu_name


class MenuElement(models.Model):
    dish_id = models.IntegerField(default=0)
    menu_id = models.IntegerField(default=0)


class AdditionalIngredient(models.Model):
    dish_for_order_id = models.IntegerField(default=0)
    ingredient = models.IntegerField(default=0)
