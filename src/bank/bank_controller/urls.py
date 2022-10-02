from django.urls import path

from .views import *

urlpatterns = [
    # User urls
    path( 'user/', RetrieveUserAPIView.as_view(), name = 'retrieve-user' ),

    # Cash account urls
    path( 'user/cash-account/', RetrieveCashAccountAPIView.as_view(), name = 'retrieve-cash_account' ),
    path( 'user/cash-account/update-pin/', UpdateCashAccountPinAPIView.as_view(), name = 'update-cash_account-pin' ),

    # Purchase urls
    path( 'user/cash-account/purchases/create/', CreatePurchaseAPIView.as_view(), name = 'create-purchase' ),
    path( 'user/cash-account/purchases/clear/', UpdatePurchaseIsIgnoreAPIView.as_view(), name = 'update-purchase-is_ignore' ),

    # Transfer urls
    path( 'user/cash-account/transfers/create/', CreateTransferAPIView.as_view(), name = 'create-transfer' ),
    path( 'user/cash-account/transfers/clear/', UpdateTransferIsIgnoreAPIView.as_view(), name = 'update-transfer-is_ignore' ),
]
