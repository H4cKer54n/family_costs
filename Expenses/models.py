from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    TYPE = (
        ('entry', 'Entrada'),
        ('exit', 'Salida'),

    )
    type = models.CharField(max_length=5, choices=TYPE, default='exit', help_text="Tipo de gasto", verbose_name="Tipo de Gasto")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto del gasto", verbose_name="Monto del Gasto")
    date = models.DateField( help_text="Fecha del gasto", verbose_name="Fecha del Gasto")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='expenses', help_text="Categoría del gasto", verbose_name="Categoría del Gasto")
    description = models.TextField(blank=True, null=True, help_text="Descripción del gasto", verbose_name="Descripción del Gasto")
    image = models.FileField(upload_to='expense_images/', null=True, blank=True, help_text="Imágen del gasto", verbose_name="Imágen del Gasto")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Fecha de creación del gasto", verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, help_text="Fecha de actualización del gasto", verbose_name="Fecha de Actualización")
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, related_name='expenses_created', help_text="Usuario que Ingreso el gasto", verbose_name="Creado por"
    )
    is_paid = models.BooleanField(default=False, help_text="Indica si el gasto ha sido pagado", verbose_name="Gasto Pagado")
    paid_date = models.DateField(null=True, blank=True, help_text="Fecha de pago del gasto", verbose_name="Fecha de Pago")


    def get_display_amount(self):
        """Devuelve el monto con signo correcto para mostrar en interfaz"""
        # Entradas (ingresos) = positivo, Salidas (gastos) = negativo
        return self.amount if self.type == 'entry' else -self.amount

    def is_image(self):
        if not self.image:
            return False
        name = self.image.name.lower()
        return any(name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'])

    def __str__(self):
        return f"{self.description} - {self.amount} on {self.date}"