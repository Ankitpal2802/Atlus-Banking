import random

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


def generate_account_number():
    """12-digit account number, guaranteed unique."""
    while True:
        number = ''.join(random.choices('0123456789', k=12))
        if not Profile.objects.filter(account_number=number).exists():
            return number


class Profile(models.Model):
    """Bank-account details for a customer, one per Django User."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    account_number = models.CharField(max_length=12, unique=True, editable=False)
    phone = models.CharField(max_length=15, blank=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_frozen = models.BooleanField(default=False, help_text="Frozen accounts can't send or receive transfers.")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = generate_account_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_username()} \u2014 {self.account_number}"


class Transaction(models.Model):
    """One ledger entry: a transfer between two accounts, or an admin adjustment."""

    KIND_TRANSFER = 'transfer'
    KIND_DEPOSIT = 'deposit'
    KIND_WITHDRAWAL = 'withdrawal'
    KIND_CHOICES = [
        (KIND_TRANSFER, 'Transfer'),
        (KIND_DEPOSIT, 'Admin deposit'),
        (KIND_WITHDRAWAL, 'Admin withdrawal'),
    ]

    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    kind = models.CharField(max_length=12, choices=KIND_CHOICES, default=KIND_TRANSFER)
    from_account = models.ForeignKey(
        Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_transactions'
    )
    to_account = models.ForeignKey(
        Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_transactions'
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    note = models.CharField(max_length=255, blank=True)
    performed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Set when an admin performed a manual deposit/withdrawal.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_kind_display()} of {self.amount} ({self.status})"
