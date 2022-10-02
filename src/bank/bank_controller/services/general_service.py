from xmlrpc.client import Boolean
from django.db.models.query import QuerySet
from django.db.models import Model

import random


def generate_pin() -> int:
    """
        Generates a pin code ( Number from 1000 to 9999 ) and returns it
    """

    return random.randint( 1000, 9999 )

def _set_ignore_status( value : bool, obj : Model ) -> None:
    """
        Sets the value 'True' for the field 'is_ignor'.
        Designed for model objects ( Purchase, Transfer and Message ).
        It is recommended not to use directly.
    """
    
    obj.is_ignore = value 
    obj.save()

def set_ignore_status_for_queryset( value : bool, queryset : QuerySet ) -> None:
    """
        Sets the "is ignore" field of all entries in the given queryset to "True"
    """

    assert isinstance( queryset, QuerySet )

    for obj in queryset:
        _set_ignore_status( value, obj )


def id_list_validate( id_list : list ) -> tuple[ bool, str ]:
    """
        Checks all values of the passed list, for suitability for use as a primary key ( id ) of such models as Purchase, Transfer, Message
    """

    error_message = None

    # Checking for a list type for id_list

    if type( id_list ) != list:
        error_message = "The 'id_list' parameter must be a list"

    # Checks each list value for a integer type

    for id in id_list:
        if type( id ) != int:
            error_message = 'One of the values in the passed list is not numeric and is not suitable for use as an identifier'
    
    # Returns True if the check succeeded, False if the check failed.

    if error_message:
        return False, error_message
    
    return True, error_message

class CurrentCashAccount:
    """
        This class was made in the likeness of rest_framework.serializers.CurrentUserDefault.
        Used as the value for the 'default' argument of rest_framework.serializers.HiddenField.

        When used this way, the HiddenField field will be equal to the user's cash_account, or a PermissionDenied exception will be thrown.
    """

    requires_context = True
    
    def __call__(self, serializer):
        return serializer.context['request'].user.cash_account
