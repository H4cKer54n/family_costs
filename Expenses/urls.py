from django.urls import path
from .views import (
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    export_csv, charts_view, CustomLoginView,
    UserListView, UserCreateView, user_change_password
)
from django.contrib.auth import views as auth_views

app_name = 'expenses'  # para usar namespaced URLs

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='expenses:login'), name='logout'),

    path('', ExpenseListView.as_view(), name='list'),
    path('add/', ExpenseCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', ExpenseUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ExpenseDeleteView.as_view(), name='delete'),
    path('export-csv/', export_csv, name='export_csv'),
    path('charts/', charts_view, name='charts'),

    # Gestión de usuarios
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/add/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/password/', user_change_password, name='user_change_password'),
]

