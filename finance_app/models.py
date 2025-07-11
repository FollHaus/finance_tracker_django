from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    CATEGORY_TYPES = (
        ('income', 'Доход'),
        ('expense', 'Расход'),
    )

    # Основные поля
    name = models.CharField(max_length=50, verbose_name='Название')
    category_type = models.CharField(
        max_length=7,
        choices=CATEGORY_TYPES,
        verbose_name='Тип категории',
        default='expense'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        null=True,  # Для системных категорий
        blank=True
    )

    # Системные категории по умолчанию
    @classmethod
    def get_default_categories(cls):
        return [
            # Доходы
            {'name': 'Зарплата', 'category_type': 'income'},
            {'name': 'Фриланс', 'category_type': 'income'},
            {'name': 'Инвестиции', 'category_type': 'income'},
            {'name': 'Подарки', 'category_type': 'income'},
            {'name': 'Другое', 'category_type': 'income'},

            # Расходы
            {'name': 'Продукты', 'category_type': 'expense'},
            {'name': 'Транспорт', 'category_type': 'expense'},
            {'name': 'Жилье', 'category_type': 'expense'},
            {'name': 'Развлечения', 'category_type': 'expense'},
            {'name': 'Одежда', 'category_type': 'expense'},
            {'name': 'Здоровье', 'category_type': 'expense'},
            {'name': 'Другое', 'category_type': 'expense'},
        ]

    @classmethod
    def get_default_category(cls, category_type):
        name = 'Другое'
        category = cls.objects.filter(
            name__iexact=name,
            category_type=category_type,
            user=None
        ).first()

        if not category:
            category = cls.objects.create(
                name=name,
                category_type=category_type,
                user=None
            )
        return category

    @classmethod
    def normalize_name(cls, name):
        """Приводит название категории к стандартному виду"""
        return name.strip().lower()

    def save(self, *args, **kwargs):
        self.name = self.normalize_name(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        unique_together = ('name', 'user', 'category_type')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'user', 'category_type'],
                name='unique_category_per_user'
            )
        ]

    def __str__(self):
        return f"{self.get_category_type_display()}: {self.name}"


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Доход'),
        ('expense', 'Расход'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(
        max_length=7,
        choices=TRANSACTION_TYPES,
        verbose_name='Тип операции'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    date = models.DateField(verbose_name='Дата')
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.amount} ({self.date})"

