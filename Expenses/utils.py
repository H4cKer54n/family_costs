from decimal import Decimal

from django.db.models import DecimalField, F, Sum, Value, Case, When

from .models import Expense


def calculate_balances(queryset=None):
    """
    Calcula los saldos:
    - saldo_real: solo movimientos pagados
    - saldo_proyectado: todos los movimientos

    Regla:
    - entry (ingreso) suma
    - exit (salida) resta
    """
    base_qs = queryset if queryset is not None else Expense.objects.all()

    signed_amount = Case(
        When(type="entry", then=F("amount")),
        When(type="exit", then=F("amount") * -1),
        default=Value(0),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    saldo_real = (
        base_qs.filter(is_paid=True).aggregate(total=Sum(signed_amount)).get("total")
        or Decimal("0")
    )
    saldo_proyectado = (
        base_qs.aggregate(total=Sum(signed_amount)).get("total") or Decimal("0")
    )

    return {
        "saldo_real": saldo_real,
        "saldo_proyectado": saldo_proyectado,
    }


def normalize_expense_amounts():
    """
    Corrige montos negativos guardados en BD y los deja en valor absoluto.
    El signo final se define por 'type' durante el cálculo (entry/exit).
    """
    updated = 0
    for expense in Expense.objects.filter(amount__lt=0):
        expense.amount = abs(expense.amount)
        expense.save(update_fields=["amount", "updated_at"])
        updated += 1
    return updated
