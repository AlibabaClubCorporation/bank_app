from rest_framework.generics import RetrieveAPIView, CreateAPIView, UpdateAPIView

from .models import *
from .serializers import *
from .permissions import CustomBasePermission
from .mixins.view_mixins import *



# User APIViews

class RetrieveUserAPIView( RetrieveAPIView ):
    """
        APIView for retrieve user data
    """

    serializer_class = RetrieveUserSerializer
    permission_classes = ( CustomBasePermission, )

    def get_object(self):
        return self.request.user

# Cash Account APIViews

class RetrieveCashAccountAPIView( RetrieveAPIView ):
    """
        APIView for retrieve cash account data
    """

    serializer_class = RetrieveCashAccountSerializer

    def get_object(self):
        return self.request.user.cash_account


class UpdateCashAccountPinAPIView( UpdateAPIView ):
    """
        APIView for update pin field in cash account
    """

    serializer_class = UpdateCashAccountPinSerializer

    def get_object(self):
        return self.request.user.cash_account


# Purchase APIViews

class CreatePurchaseAPIView( CreateAPIView ):
    """
        APIView for create purchase
    """

    serializer_class = CreatePurchaseSerializer

class UpdatePurchaseIsIgnoreAPIView( ClearHistoryMixinAPIView ):
    """
        APIView for clear history for 'transfer' objects
    """

    model = Purchase


# Transfer APIViews

class CreateTransferAPIView( CreateAPIView ):
    """
        APIView for create transfer
    """

    serializer_class = CreateTransferSerializer

class UpdateTransferIsIgnoreAPIView( ClearHistoryMixinAPIView ):
    """
        APIView for clear history for 'transfer' objects
    """

    model = Transfer