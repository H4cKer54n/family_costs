from django.urls import path
from .views import ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView, export_csv, charts_view
from django.contrib.auth import views as auth_views

app_name = 'expenses'  # para usar namespaced URLs

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='expenses:login'), name='logout'),

    path('', ExpenseListView.as_view(), name='list'),
    path('add/', ExpenseCreateView.as_view(), name='add'),
    path('edit/<int:pk>/', ExpenseUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', ExpenseDeleteView.as_view(), name='delete'),
    path('export-csv/', export_csv, name='export_csv'),
    path('charts/', charts_view, name='charts'),
]
