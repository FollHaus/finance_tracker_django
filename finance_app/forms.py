from django import forms
from .models import Transaction, Category


class TransactionForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)

        # Фильтруем категории по типу транзакции
        transaction_type = kwargs.get('initial', {}).get('transaction_type', 'expense')
        self.fields['category'].queryset = Category.objects.filter(
            user=user,
            category_type=transaction_type
        )

        # Стилизация полей
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['amount'].widget.attrs.update({'step': '0.01', 'min': '0.01'})

    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'date', 'description']