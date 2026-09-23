from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from Expenses.models import Expense
from Expenses.utils import calculate_balances


class Command(BaseCommand):
    help = (
        "Recalcula saldos (real/proyectado) y corrige montos negativos "
        "guardados en Expenses."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula los cambios sin guardar en base de datos.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        negative_qs = Expense.objects.filter(amount__lt=0).order_by("id")
        negative_count = negative_qs.count()

        self.stdout.write(self.style.WARNING("== Recalculando montos y saldos =="))
        self.stdout.write(f"Registros con monto negativo detectados: {negative_count}")

        if negative_count and dry_run:
            self.stdout.write(self.style.WARNING("Modo simulación activo: no se guardan cambios."))
            for expense in negative_qs:
                corrected = abs(expense.amount)
                self.stdout.write(
                    f"- ID {expense.id}: {expense.amount} -> {corrected} ({expense.type})"
                )
        elif negative_count:
            with transaction.atomic():
                for expense in negative_qs:
                    expense.amount = abs(expense.amount)
                    expense.save(update_fields=["amount", "updated_at"])
            self.stdout.write(self.style.SUCCESS(f"Montos corregidos: {negative_count}"))
        else:
            self.stdout.write("No hay montos negativos para corregir.")

        balances = calculate_balances(Expense.objects.all())
        saldo_real = balances["saldo_real"] or Decimal("0")
        saldo_proyectado = balances["saldo_proyectado"] or Decimal("0")

        self.stdout.write("")
        self.stdout.write("Saldos recalculados:")
        self.stdout.write(f"- Saldo real (solo pagados): {saldo_real:.2f}")
        self.stdout.write(f"- Saldo proyectado (todos): {saldo_proyectado:.2f}")
        self.stdout.write(self.style.SUCCESS("Proceso finalizado."))
