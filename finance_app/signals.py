from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        for category_data in Category.get_default_categories():
            Category.objects.get_or_create(
                name=category_data['name'],
                category_type=category_data['category_type'],
                user=None  # Системные категории
            )