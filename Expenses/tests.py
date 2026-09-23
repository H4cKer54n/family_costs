from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from Expenses.models import Expense, Category
import datetime


class ExpenseSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            first_name='Juan',
            last_name='Perez'
        )
        self.category = Category.objects.create(name='Supermercado')
        self.client = Client()

    def test_login_remember_me_extended_session(self):
        """Verifica que el login con recordar sesión configure el expiry correspondiente"""
        response = self.client.post(reverse('expenses:login'), {
            'username': 'testuser',
            'password': 'testpassword123',
            'remember_me': True
        })
        self.assertEqual(response.status_code, 302)
        # La expiración debe ser mayor a 0 (1209600 s)
        self.assertEqual(self.client.session.get_expiry_age(), 1209600)

    def test_login_no_remember_me_session(self):
        """Verifica que sin recordar sesión expire con el cierre del navegador (0)"""
        response = self.client.post(reverse('expenses:login'), {
            'username': 'testuser',
            'password': 'testpassword123',
            'remember_me': False
        })
        self.assertEqual(response.status_code, 302)
        # Cuando set_expiry(0) se invoca, get_expire_at_browser_close() es True
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_expense_list_and_dashboard_rendered(self):
        """Verifica renderizado de lista de gastos autenticado"""
        self.client.login(username='testuser', password='testpassword123')
        Expense.objects.create(
            type='exit',
            amount=150.00,
            date=datetime.date.today(),
            category=self.category,
            description='Compra de víveres',
            created_by=self.user,
            is_paid=True
        )

        response = self.client.get(reverse('expenses:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Compra de víveres')
        self.assertContains(response, 'Saldo Real')

    def test_charts_view_rendered(self):
        """Verifica que la vista de gráficos responde con los contextos adecuados"""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('expenses:charts'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('category_labels', response.context)
        self.assertIn('monthly_labels', response.context)
        self.assertIn('daily_labels', response.context)

    def test_user_list_and_create(self):
        """Verifica que el listado de usuarios y alta funcionen correctamente"""
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('expenses:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')

        # Crear nuevo usuario
        response_create = self.client.post(reverse('expenses:user_create'), {
            'username': 'maria',
            'first_name': 'Maria',
            'last_name': 'Gomez',
            'email': 'maria@example.com',
            'password1': 'StrongPass123!#',
            'password2': 'StrongPass123!#'
        })
        self.assertEqual(response_create.status_code, 302)
        self.assertTrue(User.objects.filter(username='maria').exists())

