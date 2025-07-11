from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from finance_app.models import Category


class Command(BaseCommand):
    help = 'Adds default categories for all existing users'

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            # Проверяем, есть ли уже категории у пользователя
            if not Category.objects.filter(user=user).exists():
                self.stdout.write(f'Adding categories for user: {user.username}')

                # Стандартные категории расходов
                expense_categories = [
                    'Продукты', 'Транспорт', 'Жилье', 'Развлечения',
                    'Одежда', 'Здоровье', 'Образование', 'Другое'
                ]

                # Стандартные категории доходов
                income_categories = [
                    'Зарплата', 'Фриланс', 'Инвестиции', 'Подарки', 'Другое'
                ]

                # Создаем категории
                for name in expense_categories:
                    Category.objects.create(user=user, name=name, is_income=False)

                for name in income_categories:
                    Category.objects.create(user=user, name=name, is_income=True)

                self.stdout.write(self.style.SUCCESS(f'Successfully added categories for {user.username}'))
            else:
                self.stdout.write(f'User {user.username} already has categories, skipping...')

