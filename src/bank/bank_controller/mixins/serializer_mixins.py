from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from bank_controller.services.cash_management_service import checking_availability_money
from bank_controller.services.general_service import CurrentCashAccount


class BaseCashAccountSerializer( serializers.Serializer ):
    """
        The serializer, for operations with 'cash_account'.

        Includes a function that returns cash_account, or raises a ValidationError on failure
    """

    def return_cash_account( self ):
        """
            Tries to get cash_account, raises a ValidationError if it fails
        """

        return CurrentCashAccount()(self)

class SerializerWithPinCodeValidation( BaseCashAccountSerializer ):
    """
        The serializer, for operations with 'cash_account',
        has a PIN field, a validator for this field.

        Notes:
        - Do not forget. In most cases, you won't need the "pin" field, so sometimes it needs to be removed when creating an object.
        - The "to_representation" function returns an empty dictionary, if you need to display any information, you should redefine this function
    """

    pin = serializers.IntegerField(
        min_value = 1000,
        max_value = 9999,
    )

    def validate_pin( self, value ):
        # This validator requires a 'cash_account' value in self.context
        cash_account = self.return_cash_account()

        if value == cash_account.pin:
            return value

        raise ValidationError( 'PIN entered incorrectly' )
    
    def to_representation(self, instance):
        # Redefined to not throw an error when attempting to display the "pin" argument for an object of the model being used
        return {}

class SerializerWithAmountValidation( BaseCashAccountSerializer ):
    """
        The serializer, for operations with 'cash_account',
        has a "amount" field, a validator for this field.

        Notes:
        - Requires 'cash_account' in serializer context when validating 'amount' field
    """

    amount = serializers.IntegerField( min_value = 1 )

    def validate_amount(self, value):
        cash_account = self.return_cash_account()

        if checking_availability_money( value, cash_account ):
            return value
        
        raise ValidationError( 'There are not enough funds on your cash account' )