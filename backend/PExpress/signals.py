from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, User


@receiver(post_save, sender=User)
def create_order_on_user_registration(sender, instance, created, **kwargs):
    if created:
        print(f"Order creation signal triggered for user {instance.nickname}")
        try:
            Order.objects.create(user_id=instance, courier=None, status='Подтверждение заказа')
            print("Order created successfully")
        except Exception as e:
            print(f"Error creating order: {e}")