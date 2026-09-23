from django import forms
from .models import Expense
import datetime


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['type','amount', 'date', 'category', 'description', 'image', 'is_paid', 'paid_date']

        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Introduce el monto'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Introduce una descripción'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'paid_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.update({'step': '0.01'})
        self.fields['paid_date'].required = False
        if not self.initial.get('date'):
            self.initial['date'] = datetime.date.today()
        if not self.initial.get('paid_date'):
            self.initial['paid_date'] = datetime.date.today()
