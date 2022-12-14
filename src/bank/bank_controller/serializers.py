from rest_framework import serializers
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from bank_controller.mixins.serializer_mixins import *
from bank_controller.services.general_service import CurrentCashAccount
from bank_controller.services.cash_management_service import *
from bank_controller.services.credit_service import (
    calc_amount_required_to_pay_one_credit_part,
    calc_parts_remaining_to_pay_credit,
    calc_remaining_amount_to_repay_credit,
    calc_payment_time_limit
)
from bank_controller.models import *



# User Serializers

class RetrieveUserSerializer( serializers.ModelSerializer ):
    """
        Serializer for retrieve user data
    """

    cash_account = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = model.READING_FIELDS

    def get_cash_account( self, instance ):
        # Returns a link to view information about 'cash_account', or a link to create one

        return f"{reverse( 'retrieve-cash_account' )}"


# Purchase Serializers

class PurchaseSerializer( serializers.ModelSerializer ):
    """
        Serializer for showing purchases data
    """

    class Meta:
        model = Purchase
        exclude = model.EXCLUDE_READING_FIELDS

class CreatePurchaseSerializer( SerializerWithPinCodeValidation, SerializerWithAmountValidation ):
    """
        Serializer for create purchase
    """
    
    cash_account = serializers.HiddenField( default = CurrentCashAccount() )
    merchant = serializers.CharField( max_length = 255 )

    def create(self, validated_data):
        # Includes an operation to withdraw money and remove the "pin" field to avoid further problems
        validated_data.pop( 'pin' )
        cash_withdrawal( validated_data['amount'], validated_data['cash_account'] )

        instance = Purchase.objects.create( **validated_data )

        return instance


# Transfer Serializers

class TransferSerializer( serializers.ModelSerializer ):
    """
        Serializer for showing transfers data
    """

    class Meta:
        model = Transfer
        fields = model.READING_FIELDS

class CreateTransferSerializer( SerializerWithPinCodeValidation, SerializerWithAmountValidation ):
    """
        Serializer for create transfer
    """

    sender = serializers.HiddenField( default = CurrentCashAccount() )
    reciever = serializers.PrimaryKeyRelatedField( queryset = CashAccount.objects.all() )


    def validate_sender( self, value ):
        if str(value.id) == self.initial_data['reciever']:
            raise ValidationError( 'You cannot send money from your account to your' )
        
        return value

    def create(self, validated_data):
        # Includes an operation to withdraw money and remove the "pin" field to avoid further problems

        validated_data.pop( 'pin' )
        cash_withdrawal( validated_data['amount'], validated_data['sender'] )
        cash_replenishment( validated_data['amount'], validated_data['reciever'] )

        instance = Transfer.objects.create( **validated_data )

        return instance

# Message serializers

class MessageSerializer( serializers.ModelSerializer ):
    """
        Serializer for showing messages data
    """

    class Meta:
        model = Message
        fields = model.READING_FIELDS

# Credit serializers

class CreditSerializer( serializers.ModelSerializer ):
    """
        Serializer for showing credir data
    """

    next_payment_date = serializers.SerializerMethodField()
    amount_to_pay_the_next_installment_of_the_loan = serializers.SerializerMethodField()
    remaining_amount_for_the_full_payment_of_the_loan = serializers.SerializerMethodField()
    number_of_parts_until_the_full_payment_of_the_loan = serializers.SerializerMethodField()


    class Meta:
        model = Credit
        fields = model.READING_FIELDS

    def get_next_payment_date( self, instance ):
        return calc_payment_time_limit( instance )

    def get_amount_to_pay_the_next_installment_of_the_loan( self, instance ):
        return calc_amount_required_to_pay_one_credit_part( instance )
    
    def get_remaining_amount_for_the_full_payment_of_the_loan( self, instance ):
        return calc_remaining_amount_to_repay_credit( instance )
    
    def get_number_of_parts_until_the_full_payment_of_the_loan( self, instance ):
        return calc_parts_remaining_to_pay_credit( instance )


class CreateCreditSerializer( SerializerWithPinCodeValidation ):

    cash_account = serializers.HiddenField( default = CurrentCashAccount() )
    amount = serializers.IntegerField(
        min_value = 1000,
    )
    loan_duration = serializers.ChoiceField(
        choices = ( 3, 6, 12 )
    )

    def validate_cash_account( self, value ):
        try:
            value.credit
            raise ValidationError( 'You cannot have 2 loans at the same time' )
        except ObjectDoesNotExist:
            return value

    def create(self, validated_data):
        validated_data.pop('pin')
        cash_replenishment( validated_data['amount'], validated_data['cash_account'] )

        return Credit.objects.create( **validated_data )


# Cash Account Serializers

class RetrieveCashAccountSerializer( serializers.ModelSerializer ):
    """
        Serializer for retrieve cash account data
    """

    history = serializers.SerializerMethodField()
    credit = CreditSerializer()
    messages = MessageSerializer( many = True )

    class Meta:
        model = CashAccount
        fields = model.READING_FIELDS

    def get_history( self, instance ):
        # Returns history ( All purchases and r/s transfers )

        purchases = PurchaseSerializer( data = instance.purchases.filter( is_ignore = False ), many = True )
        sent_transfers = TransferSerializer( data = instance.sent_transfers.filter( is_ignore = False ), many = True )
        recieved_transfers = TransferSerializer( data = instance.recieved_transfers.filter( is_ignore = False ), many = True )

        purchases.is_valid()
        sent_transfers.is_valid()
        recieved_transfers.is_valid()

        return {
            'purchases' : purchases.data,
            'transfers' : {
                'sent' : sent_transfers.data,
                'recieved' : recieved_transfers.data,
            }
        }


class UpdateCashAccountPinSerializer( serializers.ModelSerializer ):
    """
        Serializer for update pin field in cash account
    """

    old_pin = serializers.IntegerField( min_value = 1000, max_value = 9999 )
    new_pin = serializers.IntegerField( min_value = 1000, max_value = 9999 )

    class Meta:
        model = CashAccount
        fields = ( 'old_pin', 'new_pin' )

    def validate_old_pin( self, value ):
        if value == self.instance.pin:
            return value
        
        raise ValidationError( 'Incorrect PIN code entered' )
    
    def update(self, instance, validated_data):
        return super().update( instance, { 'pin' : validated_data.pop( 'new_pin', None ) } )

    def to_representation(self, instance):
        return {}
    