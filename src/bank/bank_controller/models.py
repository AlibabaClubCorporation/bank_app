from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator

import uuid

from bank_controller.services.general_service import generate_pin

# Create your models here.

class User( AbstractUser ):
    """
        Custom user model class
    """

    REQUIRED_FIELDS = [
        'first_name',
        'last_name',
        'email',
        'password',
    ]

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
    )

    email = models.EmailField(
        unique = True,
        editable = False,
    )

    birth_date = models.DateField(
        blank = True,
        null = True,
    )

    is_verified = models.BooleanField(
        default = False, 
    )

class CashAccount( models.Model ):
    """
        Cash account model class
    """

    id = models.UUIDField(
        default = uuid.uuid4,
        unique = True,
        primary_key = True,
        editable = False,
        db_index = True,
    )
    pin = models.PositiveSmallIntegerField(
        default = generate_pin
    )

    amount = models.PositiveIntegerField(
        default = 0,
    )

    user = models.OneToOneField(
        to = settings.AUTH_USER_MODEL,
        unique = True,
        editable = False,
        on_delete = models.PROTECT,

        related_name = 'cash_account',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    is_blocked = models.BooleanField(
        default = False,
    )


class Purchase( models.Model ):
    """
        Purchas model class
    """

    merchant = models.CharField(
        max_length = 255,
    )
    amount = models.PositiveIntegerField(
        editable = False,
    )

    cash_account = models.ForeignKey(
        to = 'bank_controller.CashAccount',
        editable = False,

        on_delete = models.CASCADE,
        related_name = 'purchases',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )
    

class Transfer( models.Model ):
    """
        Transfer model class
    """

    sender = models.ForeignKey(
        to = CashAccount,
        editable = False,

        on_delete = models.CASCADE,
        related_name = 'sent_transfers',
    )
    reciever = models.ForeignKey(
        to = CashAccount,
        editable = False,

        null = True,

        on_delete = models.SET_NULL,
        related_name = 'recieved_transfers',
    )

    amount = models.PositiveIntegerField(
        editable = False,
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
        editable = False,
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

    loan_duration_choice = (
        ( 3, 3 ),
        ( 6, 6 ),
        ( 12, 12 ),
    )

    cash_account = models.OneToOneField(
        to = CashAccount,

        editable = False,

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
        editable = False,
    )
    loan_duration = models.PositiveSmallIntegerField(
        choices = loan_duration_choice,
        editable = False,
    )

    is_increased_percentage = models.BooleanField(
        default = False,
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )
    last_payment_date = models.DateTimeField(
        auto_now_add = True,
    )


class Message( models.Model ):
    """
        Message model class
    """

    content = models.TextField()

    cash_account = models.ForeignKey(
        to = CashAccount,
        on_delete = models.CASCADE,
        related_name = 'messages',
    )

    creation_date = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )



