from decimal import Decimal

from django import forms

from .models import Profile


class AdminBalanceAdjustForm(forms.Form):
    """Teller-style manual deposit/withdrawal, used from the admin dashboard."""

    ACTION_CHOICES = [('deposit', 'Deposit'), ('withdraw', 'Withdraw')]

    account_number = forms.CharField(max_length=12)
    action = forms.ChoiceField(choices=ACTION_CHOICES)
    amount = forms.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    note = forms.CharField(max_length=255, required=False)

    def clean_account_number(self):
        account_number = self.cleaned_data['account_number'].strip()
        if not Profile.objects.filter(account_number=account_number).exists():
            raise forms.ValidationError("No account found with that number.")
        return account_number
