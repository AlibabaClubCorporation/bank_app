from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist



class IsHasCashAccount( IsAuthenticated ):
    """
        Access is allowed if user has a cash_account
    """

    def has_permission(self, request, view):
        try:
            return bool(request.user.cash_account)
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        return super().has_permission(request, view)

class CustomBasePermission( IsAuthenticated ):
    """
        Access is allowed if user.cash_account.is_blocked == False
    """

    def has_permission(self, request, view):
        try:
            return not request.user.cash_account.is_blocked
        except AttributeError:
            return False
    
    def has_object_permission(self, request, view, obj):
        return super().has_permission(request, view)