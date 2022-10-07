from django.db import models
from django.contrib.auth.models import UserManager, AbstractUser
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

import uuid

from bank_controller.services.general_service import generate_pin



# Create your models here.

class CustomUserManager(UserManager):
    """
        overridden "UserManager", to remove the need for the "username" field
    """

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = User(email=email, **extra_fields)
        user.password = make_password(password)
        user.full_name = f'{user.first_name} {user.last_name}'
        user.save(using=self._db)

        CashAccount.objects.create( user = user )
        
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        assert extra_fields['is_staff']
        assert extra_fields['is_superuser']
        return self._create_user(email, password, **extra_fields)


class User( AbstractUser ):
    """
        Custom user model class
    """

    REQUIRED_FIELDS = (
        'first_name',
        'last_name',
    )

    READING_FIELDS = (
        'id',
        'full_name',
        'email',
        'birth_date',
        'is_active',
        'cash_account',
    )

    EXCLUDE_READING_FIELDS = tuple()


    id = models.UUIDField(
        default = uuid.uuid4,
        unique = True,
        primary_key = True,
        editable = False,
        db_index = True,
    )

    first_name = models.CharField(
        max_length = 127,   
    )
    last_name = models.CharField(
        max_length = 127,   
    )

    full_name = models.CharField(
        max_length = 255,
        unique = True,

        blank = True,
    )

    email = models.EmailField(
        unique = True,
    )

    birth_date = models.DateField(
        blank = True,
        null = True,
    )

    username = None

    USERNAME_FIELD = 'email'
    objects = CustomUserManager()
    

class CashAccount( models.Model ):
    """
        Cash account model class
    """

    REQUIRED_FIELDS = (
        'user',
    )

    READING_FIELDS = (
            'id',
            'pin',
            'amount',
            'creation_date',
            'is_blocked',
            'history',
            'credit',
            'messages',
    )

    EXCLUDE_READING_FIELDS = tuple()

    id = models.UUIDField(
        default = uuid.uuid4,
        unique = True,
        primary_key = True,
        editable = False,
        db_index = True,
    )
    pin = models.PositiveSmallIntegerField(
        default = generate_pin,
        validators = [
            MinValueValidator(
                limit_value = 1000,
                message = 'Pin cannot be less than 1000 and more than 9999',
            ),
            MaxValueValidator(
                limit_value = 9999,
                message = 'Pin cannot be less than 1000 and more than 9999',
            ),
        ],
    )

    amount = models.PositiveIntegerField(
        default = 0,
    )

    user = models.OneToOneField(
        to = settings.AUTH_USER_MODEL,
        unique = True,
        on_delete = models.PROTECT,

        related_name = 'cash_account',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
    )

    is_blocked = models.BooleanField(
        default = False,
    )


class Purchase( models.Model ):
    """
        Purchas model class
    """

    REQUIRED_FIELDS = (
        'merchant',
        'cash_account',
        'amount',
    )

    READING_FIELD = '__all__'
    EXCLUDE_READING_FIELDS = ( 'cash_account', )

    merchant = models.CharField(
        max_length = 255,
    )
    amount = models.PositiveIntegerField()

    cash_account = models.ForeignKey(
        to = 'bank_controller.CashAccount',

        on_delete = models.CASCADE,
        related_name = 'purchases',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
    )

    is_ignore = models.BooleanField(
        default = False,
    )
    

class Transfer( models.Model ):
    """
        Transfer model class
    """

    REQUIRED_FIELDS = (
        'sender',
        'reciever',
        'amount',
    )

    READING_FIELDS = '__all__'
    EXCLUDE_READING_FIELDS = tuple()

    sender = models.ForeignKey(
        to = CashAccount,

        on_delete = models.CASCADE,
        related_name = 'sent_transfers',
    )
    reciever = models.ForeignKey(
        to = CashAccount,

        null = True,

        on_delete = models.SET_NULL,
        related_name = 'recieved_transfers',
    )

    amount = models.PositiveIntegerField()

    creation_date = models.DateTimeField(
        auto_now_add = True,
    )

    is_ignore = models.BooleanField(
        default = False,
    )

class Credit( models.Model ):
    """
        Credit model class

        Loan rules:
        - Loan can be taken for 3, 6 or 12 months
        - Loan amount cannot be less than 1000
        - Loan interest is fixed 0.1% of the total amount ( Every month )
        - If part of the loan has not been paid within 1 month, then the rate on the loan is doubled (0.2%) until the final payment of the loan
        - If part of the loan has not been paid again within 1 month, and the rate on the loan has already been increased, then the account is blocked (The account cannot perform operations: purchase, transfer of funds)
        * The account is blocked until the money account has the necessary amount to pay the loan in full
    """

    READING_FIELDS = (
        'amount',
        'loan_duration',
        'is_increased_percentage',
        'creation_date',
        'last_payment_date',
        'next_payment_date',
        'amount_to_pay_the_next_installment_of_the_loan',
        'remaining_amount_for_the_full_payment_of_the_loan',
        "number_of_parts_until_the_full_payment_of_the_loan",
    )

    loan_duration_choice = (
        ( 3, 3 ),
        ( 6, 6 ),
        ( 12, 12 ),
    )

    cash_account = models.OneToOneField(
        to = CashAccount,

        on_delete = models.PROTECT,
        related_name = 'credit',
    )

    amount = models.PositiveIntegerField(
        validators = [
            MinValueValidator(
                limit_value = 1000,
                message = 'The loan amount cannot be less than 1000',
            ),
        ],
    )
    amount_returned = models.PositiveIntegerField( default = 0 )

    loan_duration = models.PositiveSmallIntegerField(
        choices = loan_duration_choice,
    )

    is_increased_percentage = models.BooleanField(
        default = False,
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
    )
    last_payment_date = models.DateTimeField(
        auto_now_add = True,
    )


class Message( models.Model ):
    """
        Message model class
    """

    READING_FIELDS = (
        'content',
        'creation_date'
    )

    content = models.TextField()

    cash_account = models.ForeignKey(
        to = CashAccount,
        on_delete = models.CASCADE,
        related_name = 'messages',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
    )

    is_ignore = models.BooleanField(
        default = False,
    )



