from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Expense, Category
from django.contrib.auth.models import User
from .forms import ExpenseForm, LoginForm, UserCreateCustomForm, UserPasswordChangeCustomForm
from django.core.paginator import Paginator
from django.db.models import Sum, Q, F, Case, When, Value, DecimalField
from django.db.models.functions import TruncMonth, TruncDay
import csv
import json
from datetime import datetime, timedelta
from .utils import calculate_balances

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 10

    def get_queryset(self):
        qs = Expense.objects.all().order_by('-date')
        amount = self.request.GET.get('amount')
        category = self.request.GET.get('category')
        is_paid = self.request.GET.get('is_paid')
        type = self.request.GET.get('type')
        created_by = self.request.GET.get('created_by')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if amount:
            amount = amount.replace(',', '.')
            qs = qs.filter(amount=amount)
        if category:
            qs = qs.filter(category_id=category)
        if type:
            qs = qs.filter(type=type)
        if is_paid in ['true', 'false']:
            qs = qs.filter(is_paid=(is_paid == 'true'))
        if created_by:
            qs = qs.filter(created_by_id=created_by)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs_filtered = self.get_queryset()  # Queryset filtrado para mostrar

        # Obtener registros por página desde parámetro GET o usar valor por defecto
        per_page = self.request.GET.get('per_page', '10')
        try:
            per_page = int(per_page)
            if per_page not in [10, 25, 50, 100]:
                per_page = 10
        except ValueError:
            per_page = 10

        paginator = Paginator(qs_filtered, per_page)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['expenses'] = page_obj
        context['categories'] = Category.objects.all()
        context['users'] = User.objects.all()

        balances = calculate_balances(Expense.objects.all())
        context['total_paid'] = balances['saldo_real']
        context['total_all'] = balances['saldo_proyectado']

        # Mantener compatibilidad con el template existente
        context['total'] = balances['saldo_real']
        return context

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense_form.html'
    success_url = reverse_lazy('expenses:list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense_form.html'
    success_url = reverse_lazy('expenses:list')

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:list')


def export_csv(request):
    """Vista para exportar gastos filtrados a CSV"""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    # Obtener gastos con filtros aplicados
    expenses = Expense.objects.all().order_by('-date')

    # Aplicar los mismos filtros que en la vista de listado
    amount = request.GET.get('amount')
    category = request.GET.get('category')
    is_paid = request.GET.get('is_paid')
    type_filter = request.GET.get('type')
    created_by = request.GET.get('created_by')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if amount:
        amount = amount.replace(',', '.')
        expenses = expenses.filter(amount=amount)
    if category:
        expenses = expenses.filter(category_id=category)
    if type_filter:
        expenses = expenses.filter(type=type_filter)
    if is_paid in ['true', 'false']:
        expenses = expenses.filter(is_paid=(is_paid == 'true'))
    if created_by:
        expenses = expenses.filter(created_by_id=created_by)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)

    # Crear respuesta HTTP con CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="gastos_familiares.csv"'

    # Crear writer CSV
    writer = csv.writer(response)

    # Escribir encabezados
    writer.writerow([
        'Fecha',
        'Tipo',
        'Monto',
        'Categoría',
        'Descripción',
        'Creado por',
        'Pagado',
        'Fecha de Pago',
        'Fecha de Creación'
    ])

    # Escribir datos
    for expense in expenses:
        # Para salidas (gastos), mostrar monto negativo; para entradas (ingresos), positivo
        amount = expense.amount if expense.type == 'entry' else -expense.amount

        writer.writerow([
            expense.date.strftime('%d/%m/%Y'),
            expense.get_type_display(),
            amount,
            expense.category.name if expense.category else '',
            expense.description or '',
            expense.created_by.username,
            'Sí' if expense.is_paid else 'No',
            expense.paid_date.strftime('%d/%m/%Y') if expense.paid_date else '',
            expense.created_at.strftime('%d/%m/%Y %H:%M')
        ])

    return response


def charts_view(request):
    """Vista para mostrar gráficos de gastos e ingresos"""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)

    # Obtener parámetros de filtro
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Base queryset
    expenses = Expense.objects.all()

    # Aplicar filtros de fecha si existen
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)

    # 1. Datos para gráfico de dona: Gastos por categoría
    category_data = expenses.filter(type='exit').values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    category_labels = [item['category__name'] or 'Sin categoría' for item in category_data]
    category_values = [float(item['total']) for item in category_data]

    # 2. Datos para gráfico de barras: Gastos vs Ingresos por mes
    monthly_data = expenses.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        ingresos=Sum(
            Case(
                When(type='entry', then=F('amount')),
                default=Value(0),
                output_field=DecimalField(),
            )
        ),
        gastos=Sum(
            Case(
                When(type='exit', then=F('amount')),
                default=Value(0),
                output_field=DecimalField(),
            )
        )
    ).order_by('month')

    monthly_labels = [item['month'].strftime('%Y-%m') for item in monthly_data]
    monthly_ingresos = [float(item['ingresos']) for item in monthly_data]
    monthly_gastos = [float(item['gastos']) for item in monthly_data]

    # 3. Datos para gráfico de líneas: Balance diario (últimos 30 días si no hay filtro)
    if not date_from and not date_to:
        # Últimos 30 días
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        daily_expenses = expenses.filter(date__gte=start_date, date__lte=end_date)
    else:
        daily_expenses = expenses

    daily_data = daily_expenses.annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        ingresos=Sum(
            Case(
                When(type='entry', then=F('amount')),
                default=Value(0),
                output_field=DecimalField(),
            )
        ),
        gastos=Sum(
            Case(
                When(type='exit', then=F('amount')),
                default=Value(0),
                output_field=DecimalField(),
            )
        )
    ).order_by('day')

    daily_labels = [item['day'].strftime('%d/%m') for item in daily_data]
    daily_ingresos = [float(item['ingresos']) for item in daily_data]
    daily_gastos = [float(item['gastos']) for item in daily_data]

    # Calcular totales para mostrar
    total_ingresos = sum(monthly_ingresos)
    total_gastos = sum(monthly_gastos)
    balance = total_ingresos - total_gastos

    context = {
        'category_labels': json.dumps(category_labels),
        'category_values': json.dumps(category_values),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_ingresos': json.dumps(monthly_ingresos),
        'monthly_gastos': json.dumps(monthly_gastos),
        'daily_labels': json.dumps(daily_labels),
        'daily_ingresos': json.dumps(daily_ingresos),
        'daily_gastos': daily_gastos,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': balance,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'charts.html', context)


class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if remember_me:
            # 2 semanas (14 días en segundos)
            self.request.session.set_expiry(1209600)
        else:
            # Expira cuando el navegador se cierra
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'user_list.html'
    context_object_name = 'user_list'
    ordering = ['username']


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreateCustomForm
    template_name = 'user_form.html'
    success_url = reverse_lazy('expenses:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Usuario '{self.object.username}' creado con éxito.")
        return response


@login_required
def user_change_password(request, pk):
    target_user = get_object_or_404(User, pk=pk)

    # Permitir que el usuario cambie su propia contraseña o que un superuser/staff cambie la de otros
    if request.user != target_user and not request.user.is_staff:
        messages.error(request, "No tienes permisos para modificar la contraseña de otro usuario.")
        return redirect('expenses:user_list')

    if request.method == 'POST':
        form = UserPasswordChangeCustomForm(user=target_user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contraseña actualizada para '{target_user.username}'.")
            return redirect('expenses:user_list')
    else:
        form = UserPasswordChangeCustomForm(user=target_user)

    return render(request, 'user_password_change.html', {
        'form': form,
        'target_user': target_user
    })
