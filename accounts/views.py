from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdminBalanceAdjustForm
from .models import Profile, Transaction

# ---------------------------------------------------------------------------
# Public landing 
# ---------------------------------------------------------------------------

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('accounts:admin_dashboard')
        return redirect('accounts:dashboard')
    return render(request, 'accounts/home.html')


@login_required(login_url='accounts:login')
def dashboard(request):
    if request.user.is_staff:
        return redirect('accounts:admin_dashboard')
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'accounts/dashboard.html', {'profile': profile})


# ---------------------------------------------------------------------------
# Customer auth 
# ---------------------------------------------------------------------------

def customer_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')

    error = None
    posted_email = ''

    if request.method == 'POST':
        posted_email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=posted_email, password=password) \
            if _user_exists(posted_email) else None

        if user is not None:
            login(request, user)
            return redirect('accounts:home')

        if not _user_exists(posted_email):
            error = "Email does not match"
        else:
            error = "Password does not match"

    return render(request, 'accounts/login.html', {'error': error, 'posted_email': posted_email})


def _user_exists(email):
    return User.objects.filter(email__iexact=email).exists()


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts:home')

    errors = []
    success = None
    posted = {}

    if request.method == 'POST':
        full_name = request.POST.get('fullname', '').strip()
        email = request.POST.get('email', '').strip()
        account_number = request.POST.get('Account', '').strip()
        password = request.POST.get('password', '')
        password_repeat = request.POST.get('repeat_password', '')
        posted = {'fullname': full_name, 'email': email, 'account': account_number}

        if not full_name or not email or not password or not account_number or not password_repeat:
            errors.append("All fields are required")

        try:
            validate_email(email)
        except ValidationError:
            errors.append("Email is not valid")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if password != password_repeat:
            errors.append("Password does not match")

        if email and User.objects.filter(email__iexact=email).exists():
            errors.append("Email already exists!")

        if account_number and Profile.objects.filter(account_number=account_number).exists():
            errors.append("That account number is already registered.")

        if account_number and not account_number.isdigit():
            errors.append("Account number must contain digits only.")

        if not errors:
            first, _, last = full_name.partition(' ')
            username = email  # login uses email, but Django's User needs a username too
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first, last_name=last,
            )
            Profile.objects.create(user=user, account_number=account_number)
            success = "You are registered successfully."
            posted = {}

    return render(request, 'accounts/register.html', {
        'errors': errors, 'success': success, 'posted': posted,
    })


def logout_view(request):
    logout(request)
    return redirect('accounts:home')


# ---------------------------------------------------------------------------
# Money transfer 
# ---------------------------------------------------------------------------

@login_required(login_url='accounts:login')
def transfer_page(request):
    profile = get_object_or_404(Profile, user=request.user)
    return render(request, 'accounts/transfer.html', {'profile': profile})


@login_required(login_url='accounts:login')
def transfer_submit(request):
    """AJAX endpoint used by script.js. Returns plain text/HTML, same
    contract as the original transfer.php, so the front end is unchanged."""
    if request.method != 'POST':
        return HttpResponse("Error: invalid request method.", status=405)

    profile = get_object_or_404(Profile, user=request.user)

    if profile.is_frozen:
        return HttpResponse("Error: your account is frozen.", status=400)

    to_account_number = request.POST.get('toAccount', '').strip()
    amount_raw = request.POST.get('amount', '').strip()

    if not to_account_number:
        return HttpResponse("Error: recipient account is required.", status=400)

    try:
        amount = Decimal(amount_raw)
    except (InvalidOperation, ValueError):
        return HttpResponse("Error: invalid amount.", status=400)

    if amount <= 0:
        return HttpResponse("Error: amount must be greater than zero.", status=400)

    if to_account_number == profile.account_number:
        return HttpResponse("Error: you can't transfer to your own account.", status=400)

    if not Profile.objects.filter(account_number=to_account_number).exists():
        return HttpResponse("Error: Recipient account not found.", status=400)

    with transaction.atomic():
        sender = Profile.objects.select_for_update().get(pk=profile.pk)
        recipient = Profile.objects.select_for_update().get(account_number=to_account_number)

        if recipient.is_frozen:
            return HttpResponse("Error: recipient account can't receive transfers.", status=400)

        if sender.balance < amount:
            return HttpResponse("Error: Insufficient balance.", status=400)

        sender.balance -= amount
        recipient.balance += amount
        sender.save(update_fields=['balance'])
        recipient.save(update_fields=['balance'])

        Transaction.objects.create(
            kind=Transaction.KIND_TRANSFER,
            from_account=sender,
            to_account=recipient,
            amount=amount,
            status=Transaction.STATUS_SUCCESS,
        )

    return HttpResponse("Money transferred successfully.")


@login_required(login_url='accounts:login')
def my_account(request):
    profile = get_object_or_404(Profile, user=request.user)
    txns = Transaction.objects.filter(Q(from_account=profile) | Q(to_account=profile))
    return render(request, 'accounts/my_account.html', {'profile': profile, 'txns': txns})


@login_required(login_url='accounts:login')
def change_password(request):
    """Wired up from the 'Set Online Banking Password' service card."""
    error = None
    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')

        if not request.user.check_password(current):
            error = "Current password is incorrect."
        elif len(new_password) < 8:
            error = "New password must be at least 8 characters long."
        elif new_password != confirm:
            error = "New password and confirmation don't match."
        else:
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)  # keep the session alive after the password change
            messages.success(request, "Your password has been updated.")
            return redirect('accounts:my_account')

    return render(request, 'accounts/change_password.html', {'error': error})


# ---------------------------------------------------------------------------
# Admin area
# ---------------------------------------------------------------------------

def _is_staff(user):
    return user.is_authenticated and user.is_staff


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('accounts:admin_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('accounts:admin_dashboard')
        error = "Invalid admin credentials."

    return render(request, 'accounts/admin_login.html', {'error': error})


@user_passes_test(_is_staff, login_url='accounts:admin_login')
def admin_dashboard(request):
    adjust_form = AdminBalanceAdjustForm()

    if request.method == 'POST':
        adjust_form = AdminBalanceAdjustForm(request.POST)
        if adjust_form.is_valid():
            account_number = adjust_form.cleaned_data['account_number']
            action = adjust_form.cleaned_data['action']
            amount = adjust_form.cleaned_data['amount']
            note = adjust_form.cleaned_data['note']

            with transaction.atomic():
                account = Profile.objects.select_for_update().get(account_number=account_number)

                if action == 'withdraw' and account.balance < amount:
                    messages.error(request, "Can't withdraw more than the account balance.")
                    return redirect('accounts:admin_dashboard')

                if action == 'deposit':
                    account.balance += amount
                    kind = Transaction.KIND_DEPOSIT
                else:
                    account.balance -= amount
                    kind = Transaction.KIND_WITHDRAWAL

                account.save(update_fields=['balance'])
                Transaction.objects.create(
                    kind=kind,
                    to_account=account if action == 'deposit' else None,
                    from_account=account if action == 'withdraw' else None,
                    amount=amount,
                    status=Transaction.STATUS_SUCCESS,
                    note=note,
                    performed_by=request.user,
                )

            messages.success(request, f"{action.title()} of \u20b9{amount} applied to {account_number}.")
            return redirect('accounts:admin_dashboard')

    profiles = Profile.objects.select_related('user').order_by('-created_at')
    recent_txns = Transaction.objects.select_related('from_account__user', 'to_account__user')[:25]

    return render(request, 'accounts/admin_dashboard.html', {
        'profiles': profiles,
        'recent_txns': recent_txns,
        'adjust_form': adjust_form,
    })


@user_passes_test(_is_staff, login_url='accounts:admin_login')
def admin_edit_user(request, user_id):
    """Admin can change any customer's data \u2014 name, email, phone, account
    number, balance, frozen status, or reset their password."""
    customer_user = get_object_or_404(User, pk=user_id, is_staff=False)
    profile = get_object_or_404(Profile, user=customer_user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        balance_raw = request.POST.get('balance', '').strip()
        is_frozen = request.POST.get('is_frozen') == '1'
        new_password = request.POST.get('new_password', '').strip()

        errors = []

        if email and User.objects.filter(email__iexact=email).exclude(pk=customer_user.pk).exists():
            errors.append("Another account already uses that email.")

        if account_number != profile.account_number and \
                Profile.objects.filter(account_number=account_number).exclude(pk=profile.pk).exists():
            errors.append("Another account already uses that account number.")

        try:
            balance = Decimal(balance_raw)
        except (InvalidOperation, ValueError):
            errors.append("Balance must be a valid number.")
            balance = profile.balance

        if not errors:
            customer_user.first_name = first_name
            customer_user.last_name = last_name
            customer_user.email = email
            customer_user.username = email or customer_user.username
            if new_password:
                customer_user.password = make_password(new_password)
            customer_user.save()

            profile.phone = phone
            profile.account_number = account_number
            profile.balance = balance
            profile.is_frozen = is_frozen
            profile.save()

            messages.success(request, "Customer details updated.")
            return redirect('accounts:admin_dashboard')

        for e in errors:
            messages.error(request, e)

    return render(request, 'accounts/admin_edit_user.html', {
        'customer_user': customer_user,
        'profile': profile,
    })
