from django.contrib.auth.models import User
from django.db import models
from django.forms import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from .forms import TransactionForm


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Добро пожаловать, {username}!")
                return redirect('dashboard')
        else:
            messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = AuthenticationForm()
    return render(request, 'finance_app/registration/login.html', {'form': form})



from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно!")
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'finance_app/registration/register.html', {'form': form})

@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Вы успешно вышли из системы.")
    return redirect('login')


from django.contrib.auth.decorators import login_required
from django.db.models import Sum


@login_required
def dashboard(request):
    user = request.user

    # Проверяем, есть ли импортированные транзакции в сессии
    imported_ids = request.session.pop('imported_transactions', None)

    if imported_ids:
        # Получаем импортированные транзакции
        imported_transactions = Transaction.objects.filter(
            id__in=imported_ids
        ).order_by('-date', '-created_at')

        # Получаем остальные транзакции (кроме импортированных)
        other_transactions = Transaction.objects.filter(
            user=user
        ).exclude(
            id__in=imported_ids
        ).order_by('-date', '-created_at')[:10 - len(imported_ids)]

        # Объединяем два QuerySet
        recent_transactions = list(imported_transactions) + list(other_transactions)
    else:
        # Обычный запрос если нет импортированных транзакций
        recent_transactions = Transaction.objects.filter(
            user=user
        ).order_by('-date', '-created_at')[:10]

    # Рассчитываем баланс
    income = Transaction.objects.filter(
        user=user,
        transaction_type='income'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    expenses = Transaction.objects.filter(
        user=user,
        transaction_type='expense'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    balance = income - expenses

    # Данные для графиков
    expense_categories = (
        Transaction.objects
        .filter(user=request.user, transaction_type='expense')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    income_categories = (
        Transaction.objects
        .filter(user=request.user, transaction_type='income')
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    context = {
        'balance': balance,
        'income': income,
        'expenses': expenses,
        'recent_transactions': recent_transactions,
        'expense_categories': expense_categories,
        'income_categories': income_categories,
    }

    return render(request, 'finance_app/dashboard.html', context)


from django.contrib.auth.decorators import login_required


@login_required
def add_transaction(request):
    # Получаем все категории пользователя + системные
    categories = Category.objects.filter(
        models.Q(user=request.user) | models.Q(user=None))

    if request.method == 'POST':
         try:
            transaction = Transaction(
                user=request.user,
                transaction_type=request.POST.get('transaction_type'),
                amount=request.POST.get('amount'),
                category_id=request.POST.get('category'),
                date=request.POST.get('date'),
                description=request.POST.get('description', '')
            )
            transaction.save()
            messages.success(request, 'Транзакция успешно добавлена!')
            return redirect('dashboard')
         except Exception as e:
            messages.error(request, f'Ошибка при добавлении транзакции: {e}')

    return render(request, 'finance_app/add_transaction.html', {
        'categories': categories
    })


@login_required
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Транзакция успешно обновлена!')
            return redirect('dashboard')
    else:
        form = TransactionForm(request.user, instance=transaction)

    return render(request, 'finance_app/edit_transaction.html', {'form': form, 'transaction': transaction})


@login_required
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Транзакция успешно удалена!')
        return redirect('dashboard')

    return render(request, 'finance_app/delete_transaction.html', {'transaction': transaction})


import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Transaction, Category


@login_required
def export_transactions(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Дата', 'Тип', 'Категория', 'Сумма', 'Описание'])

    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    for t in transactions:
        writer.writerow([
            t.date.strftime('%Y-%m-%d'),
            t.get_transaction_type_display(),
            t.category.name if t.category else '',
            t.amount,
            t.description
        ])

    return response


@login_required
def import_transactions(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Пожалуйста, загрузите файл в формате CSV')
            return redirect('import_transactions')

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            imported_transactions = []
            for row in reader:
                if not any(row.values()):  # Пропускаем пустые строки
                    continue

                # Нормализуем данные
                category_name = row['Категория'].strip().lower()
                transaction_type = 'income' if row['Тип'].strip().lower() == 'доход' else 'expense'

                # Ищем категорию (сначала пользовательские, потом системные)
                category = Category.objects.filter(
                    models.Q(user=request.user) | models.Q(user=None),
                    name__iexact=category_name,
                    category_type=transaction_type
                ).first()

                # Если категория не найдена - используем категорию "Другое"
                if not category:
                    default_category_name = 'другое'
                    category = Category.objects.filter(
                        models.Q(user=request.user) | models.Q(user=None),
                        name__iexact=default_category_name,
                        category_type=transaction_type
                    ).first()

                    # Если даже "Другое" нет - создаем системную
                    if not category:
                        category = Category.objects.create(
                            name=default_category_name.capitalize(),
                            category_type=transaction_type,
                            user=None  # Системная категория
                        )

                # Создаем транзакцию
                try:
                    transaction = Transaction.objects.create(
                        user=request.user,
                        date=row['Дата'].strip(),
                        transaction_type=transaction_type,
                        category=category,
                        amount=row['Сумма'].strip(),
                        description=row.get('Описание', '').strip()
                    )
                    imported_transactions.append(transaction)
                except Exception as e:
                    messages.warning(request, f'Ошибка при создании транзакции: {str(e)}')

            request.session['imported_transactions'] = [t.id for t in imported_transactions]
            messages.success(request, f'Успешно импортировано {len(imported_transactions)} транзакций')
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'Ошибка при импорте: {str(e)}')

    return render(request, 'finance_app/import_transactions.html')