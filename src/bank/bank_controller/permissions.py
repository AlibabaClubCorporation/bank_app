from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist


class CustomBasePermission( IsAuthenticated ):
    """
        Access is allowed if the user's 'is_active' flag is set to 'True'
    """

    def has_permission(self, request, view):
        parent_result = super().has_permission( request, view )
        return request.user.is_active and parent_result

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class IsHasCashAccount( CustomBasePermission ):
    """
        Access is allowed if the user has a cash_account
    """

    def has_permission(self, request, view):
        # Returns True if User.is_active == True and if the user has a cash_account and if cash_account.is_blocked == False, otherwise False

        parent_result = super().has_permission( request, view )
        is_has_cash_account = False
        is_blocked_cash_account = True
        
        try:
            is_blocked_cash_account = request.user.cash_account.is_blocked
            is_has_cash_account = True
        except (ObjectDoesNotExist, AttributeError):
            pass

        return parent_result and is_has_cash_account and not is_blocked_cash_account

    def has_object_permission(self, request, view, obj):
        self.has_permission( request, view )
