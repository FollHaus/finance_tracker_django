from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

from .views import export_transactions, import_transactions

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('transactions/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('transactions/export/', export_transactions, name='export_transactions'),
    path('transactions/import/', import_transactions, name='import_transactions'),

]