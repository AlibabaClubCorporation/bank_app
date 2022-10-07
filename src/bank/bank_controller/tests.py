import datetime
from time import sleep

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.db.utils import IntegrityError
from django.test import TestCase
from django.conf import settings

from bank_controller.models import *
from bank_controller.serializers import *
from bank_controller.services.cash_management_service import *
from bank_controller.services.general_service import *
from bank_controller.services.credit_service import *
from bank_controller.mixins.serializer_mixins import *
from bank_controller.mixins.view_mixins import *


class PseudoRequest():
    user = None
    data = None

# View tests

class CustomAPITestCase( APITestCase ):
    """
        Redefined class APITestCase, to implement the necessary functions for tests:
        - authenticate_user
        - unauthenticated
        And also to set the standard template for the "set_up()" function
    """

    def authenticate_user( self, user : User ) -> None:
        """
            Function, accepts an object of type User, creates or re-creates a Token, which then writes to the HEADERS of the request
        """
        
        try:
            self.token = Token.objects.create( user = user )
        except IntegrityError:
            self.token.delete()
            self.token = Token.objects.create( user = user )

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def unauthenticated( self ) -> None:
        """
            Clears the HTTP_AUTHORIZATION setting for the HEADERS request
        """

        self.client.credentials( HTTP_AUTHORIZATION = '' )

    def set_amount_to_cash_account( self, cash_account : CashAccount, amount : int ) -> None:
        """
            Sets 'cash_account.amount' to the value of 'amount'
        """

        cash_account.amount = amount
        cash_account.save()


    def setUp(self) -> None:
        # Creates two users needed to test different functionality

        self.user_first = User.objects.create_user( 'mrloking11@gmail.com', '123456', first_name = 'Oleg', last_name = 'Zdorov' )
        self.user_first.is_active = True
        self.user_first.save()
        self.user_second = User.objects.create_user( 'Art@gmail.com', '123456', first_name = 'Serhiy', last_name = 'Zdorov' )
        self.user_second.is_active = True
        self.user_second.save()


class TestUserAPIViews( CustomAPITestCase ):

    def test_retrieve( self ):
        url = reverse('retrieve-user')
        data = {}

        user_list = ( self.user_first, self.user_second )

        for i in range( len( user_list ) ):
            self.authenticate_user( user_list[i] )
            response = self.client.get(url, data, format='json')

            cash_account_data = RetrieveUserSerializer( instance = user_list[i] ).data

            # Checking code status
            self.assertEqual( response.status_code, status.HTTP_200_OK )
            #  Checking the correctness of the output data
            self.assertEqual( response.data, cash_account_data )
        
        self.unauthenticated()
        response = self.client.get(url, data, format='json')

        # Checking the code status for an unauthorized user
        self.assertEqual( response.status_code, status.HTTP_401_UNAUTHORIZED )


class TestCashAccountAPIViews( CustomAPITestCase ):

    def test_retrieve( self ):
        url = reverse('retrieve-cash_account')
        data = {}

        user_list = ( self.user_first, self.user_second )

        for i in range( len( user_list ) ):
            self.authenticate_user( user_list[i] )
            response = self.client.get(url, data, format='json')

            cash_account_data = RetrieveCashAccountSerializer( instance = user_list[i].cash_account ).data

            # Checking code status
            self.assertEqual( response.status_code, status.HTTP_200_OK )
            #  Checking the correctness of the output data
            self.assertEqual( response.data, cash_account_data )
        
        self.unauthenticated()
        response = self.client.get(url, data, format='json')

        # Checking the code status for an unauthorized user
        self.assertEqual( response.status_code, status.HTTP_401_UNAUTHORIZED )


    def test_update_pin( self ):
        url = reverse('update-cash_account-pin')

        user_list = ( self.user_first, self.user_second )
        new_pin = 1000

        for i in range( len( user_list ) ):
            self.authenticate_user( user_list[i] )
            data = { 'new_pin' : new_pin, 'old_pin' : user_list[i].cash_account.pin }

            response = self.client.put(url, data, format='json')

            # Checking status code
            self.assertEqual( response.status_code, status.HTTP_200_OK )

            current_pin = CashAccount.objects.get( pk = user_list[i].cash_account.pk ).pin

            # Checking to change the old pin to a new one
            self.assertEqual( new_pin, current_pin )

        self.unauthenticated()
        response = self.client.get(url, data, format='json')

        # Checking the code status for an unauthorized user
        self.assertEqual( response.status_code, status.HTTP_401_UNAUTHORIZED )

class TestPurchaseAPIViews( CustomAPITestCase ):

    def test_create( self ):
        url = reverse('create-purchase')

        user_list = ( self.user_first, self.user_second )

        for i in range( len( user_list ) ):
            self.authenticate_user( user_list[i] )
            data = { 
                'pin' : user_list[i].cash_account.pin,
                'merchant' : 'Iphone X',
                'amount' : 1000,
            }

            self.set_amount_to_cash_account( user_list[i].cash_account, amount = 1013 )

            response = self.client.post(url, data, format='json')

            # Checking status code
            self.assertEqual( response.status_code, status.HTTP_201_CREATED )

            instance = CashAccount.objects.get( user = user_list[i] ).purchases.first()
            serializer_data = PurchaseSerializer( instance = instance ).data
            purchase_data = {
                'merchant' : serializer_data['merchant'],
                'amount' : serializer_data['amount'],
            }

            data.pop('pin')

            # Checking the correctness of the created Purchase
            self.assertEqual( data, purchase_data )

            # Correctness of debiting payment for the purchase
            self.assertEqual( instance.cash_account.amount, 13 )

        self.unauthenticated()
        response = self.client.post(url, {}, format='json')

        # Checking the code status for an unauthorized user
        self.assertEqual( response.status_code, status.HTTP_401_UNAUTHORIZED )

class TestTransferAPIViews( CustomAPITestCase ):

    def test_create( self ):
        url = reverse('create-transfer')
        self.authenticate_user( self.user_first )
        data = { 
            'pin' : self.user_first.cash_account.pin,
            'reciever' : self.user_second.cash_account.pk,
            'amount' : 1000,
        }

        self.set_amount_to_cash_account( self.user_first.cash_account, amount = 1013 )
        self.set_amount_to_cash_account( self.user_second.cash_account, amount = 1013 )

        response = self.client.post(url, data, format='json')

        # Checking status code
        self.assertEqual( response.status_code, status.HTTP_201_CREATED )

        sent_transfer_instance = CashAccount.objects.get( user = self.user_first ).sent_transfers.first()
        recieved_transfer_instance = CashAccount.objects.get( user = self.user_second ).recieved_transfers.first()
        sent_transfer_serializer_data = TransferSerializer( instance = sent_transfer_instance ).data
        sent_transfer_data = {
            'sender' : sent_transfer_serializer_data['sender'],
            'reciever' : sent_transfer_serializer_data['reciever'],
            'amount' : sent_transfer_serializer_data['amount'],
        }

        data.pop('pin')
        data['sender'] = self.user_first.cash_account.pk

        # Checking the correctness of the created Purchase
        self.assertEqual( data, sent_transfer_data )

        # Checking the correctness of withdrawing the account after sending the transfer
        self.assertEqual( sent_transfer_instance.sender.amount, 13 )
        # Checking the correctness of the account replenishment after receiving the transfer
        self.assertEqual( recieved_transfer_instance.reciever.amount, 2013 )


        self.unauthenticated()
        response = self.client.post(url, {}, format='json')

        # Checking the code status for an unauthorized user
        self.assertEqual( response.status_code, status.HTTP_401_UNAUTHORIZED )

# View mixins tests

class TestClearHistoryMixinAPIView( TestCase ):

    def test_as_view( self ):
        view = ClearHistoryMixinAPIView
        
        try:
            view.as_view()
            raise AssertionError
        except AttributeError:
            pass

        view.model = 1

        try:
            view.as_view()
            raise AssertionError
        except AttributeError:
            pass

        view.model = CashAccount

        try:
            view.as_view()
            raise AssertionError
        except AttributeError:
            pass

        view.model = Purchase

        try:
            view.as_view()
        except AttributeError:
            raise AssertionError
    
    def test_put( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.save()

        for i in range( 1, 11 ): 
            Purchase.objects.create( merchant = str(i), amount = 10, cash_account = user.cash_account )

        view = ClearHistoryMixinAPIView
        view.model = Purchase

        request = PseudoRequest
        request.user = user
        request.data = {
        'id_list' : [ 1, 3 ]
        }

        view.put( request )

        for i in range( 1, 11 ):
            purchase = Purchase.objects.get( pk = i )
            
            if i in ( 1, 3 ):
                self.assertEqual( True, purchase.is_ignore )
                continue
                
            self.assertEqual( False, purchase.is_ignore )

        request.data = {}

        view.put( request )

        for i in range( 1, 11 ):
            purchase = Purchase.objects.get( pk = i )

            self.assertEqual( True, purchase.is_ignore )

        request.data = { "id_list" : ( 1, "a" ) }

        responce = view.put( request )

        self.assertEqual( 400, responce.status_code )

# Serializer tests

class TestCreatePurchaseSerializer( TestCase ):

    def test_valid_data( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1013
        user.cash_account.save()
        user.save()

        shipping_data = {
            'pin' : user.cash_account.pin,
            'merchant' : 'Pills',
            'amount' : 1000,
        }

        result_data = CreatePurchaseSerializer( data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        result_data.is_valid()
        result_data.create( result_data.validated_data )
        
        result_data = user.cash_account.purchases.first()

        # Checking the correctness of the data of the created Purchase
        self.assertEqual( result_data.merchant, shipping_data['merchant'] )
        self.assertEqual( result_data.amount, shipping_data['amount'] )
        self.assertEqual( result_data.cash_account.pk, user.cash_account.pk )

        # Checking the withdrawal of the amount, and whether Purchase is tied to cash_account
        self.assertEqual( user.cash_account.amount, 13 )
        self.assertEqual( user.cash_account.purchases.count(), 1 )


    def test_invalid_pin( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1013
        user.cash_account.save()
        user.save()

        pin = 1000
        if pin == user.cash_account.pin:
            pin = 1001

        shipping_data = {
            'pin' : pin,
            'merchant' : 'None',
            'amount' : 1015,
        }

        result_data = CreatePurchaseSerializer( data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        is_valid_result = result_data.is_valid()

        # Error checking
        self.assertEqual( is_valid_result, False )
        self.assertEqual( str(result_data.errors['pin'][0]), 'PIN entered incorrectly')
        self.assertEqual( str(result_data.errors['amount'][0]), 'There are not enough funds on your cash account')

        # Checks that the account on the account remains unchanged, and checks for the absence of Purchase
        self.assertEqual( user.cash_account.amount, 1013 )
        self.assertEqual( user.cash_account.purchases.count(), 0 )

class TestCreateTransferSerializer( TestCase ):

    def test_valid_data( self ):
        
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1013
        user.cash_account.save()
        user.save()
        user2 = User.objects.create_user( email = 'mrloking12@gmail.com', first_name = 'Lor', last_name = 'ha', password = '123456' )
        user2.cash_account.amount = 0
        user2.cash_account.save()
        user2.save()

        shipping_data = {
            'pin' : user.cash_account.pin,
            'amount' : 1000,
            'reciever' : user2.cash_account.pk,
        }

        result_data = CreateTransferSerializer( data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        result_data.is_valid()
        result_data.create( result_data.validated_data )

        # Checking the write-off and recording of the amount from the sender's account to the recipient's account
        self.assertEqual( user.cash_account.amount, 13 )
        self.assertEqual( Transfer.objects.get( reciever = user2.cash_account ).reciever.amount, 1000 )
        self.assertEqual( user.cash_account.sent_transfers.first().pk, user2.cash_account.recieved_transfers.first().pk )

    def test_invalid_data( self ):
        
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1013
        user.cash_account.save()
        user.save()
        user2 = User.objects.create_user( email = 'mrloking12@gmail.com', first_name = 'Lor', last_name = 'ha', password = '123456' )
        user2.cash_account.amount = 0
        user2.cash_account.save()
        user2.save()

        pin = 1000
        if pin == user.cash_account.pin:
            pin = 1001

        shipping_data = {
            'pin' : pin,
            'amount' : 1014,
            'reciever' : 1234,
        }

        result_data = CreateTransferSerializer( data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        result_data.is_valid()

        errors = result_data.errors

        self.assertEqual( str(errors['pin'][0]), 'PIN entered incorrectly' )
        self.assertEqual( str(errors['amount'][0]), 'There are not enough funds on your cash account' )
        self.assertEqual( str(errors['reciever'][0].code), 'does_not_exist' )
        
        
class TestUpdateCashAccountPinSerialzer( TestCase ):

    def test_valid_data( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.save()

        shipping_data = {
            'old_pin' : user.cash_account.pin,
            'new_pin' : 1000,
        }

        expected_result = {
            'pin' : 1000
        }

        result_data = UpdateCashAccountPinSerializer( instance = user.cash_account,data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        result_data.is_valid()
        result_data = result_data.update( instance = user.cash_account, validated_data = result_data.validated_data )

        # Checks if the pin has changed
        self.assertEqual( expected_result['pin'], result_data.pin )

    def test_invalid_data( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.save()

        pin = 1000
        if pin == user.cash_account.pin:
            pin = 1001

        shipping_data = {
            'old_pin' : pin,
            'new_pin' : 1000,
        }

        result_data = UpdateCashAccountPinSerializer( instance = user.cash_account,data = shipping_data )
        result_data.context['request'] = PseudoRequest
        result_data.context['request'].user = user

        result_data.is_valid()

        errors = result_data.errors

        self.assertEqual( str(errors['old_pin'][0]), 'Incorrect PIN code entered' )

# Serializer mixins tests

class TestSerializerWithAmountValidation( TestCase ):

    def test( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1000
        user.cash_account.save()
        user.save()

        amount = user.cash_account.amount

        serializer = SerializerWithAmountValidation()
        serializer.context['request'] = PseudoRequest
        serializer.context['request'].user = user

        self.assertEqual( 1000, serializer.validate_amount( amount ) )

        try:
            serializer.validate_amount( amount + 1 )
            raise AssertionError
        except ValidationError:
            pass

class TestSerializerWithPinCodeValidation( TestCase ):

    def test( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.pin = 1000
        user.cash_account.save()
        user.save()

        pin = user.cash_account.pin

        serializer = SerializerWithPinCodeValidation()
        serializer.context['request'] = PseudoRequest
        serializer.context['request'].user = user

        self.assertEqual( 1000, serializer.validate_pin( pin ) )

        try:
            serializer.validate_pin( pin + 1 )
            raise AssertionError
        except ValidationError:
            pass

# Service tests

class TestCashManagementService( TestCase ):

    def test_checking_availability_money( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1000
        user.cash_account.save()
        user.save()

        self.assertEqual( False, checking_availability_money( 1001, user.cash_account ) )
        self.assertEqual( True, checking_availability_money( 1000, user.cash_account ) )
        self.assertEqual( True, checking_availability_money( 2, user.cash_account ) )
    
    def test_cash_withdrawal( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1000
        user.cash_account.save()
        user.save()

        self.assertEqual( True, cash_withdrawal( 1000, user.cash_account ) )
        self.assertEqual( 0, user.cash_account.amount )

        user.cash_account.amount = 1000
        user.cash_account.save()

        self.assertEqual( False, cash_withdrawal( 1001, user.cash_account ) )
        self.assertEqual( 1000, user.cash_account.amount )

    def test_cash_replenishment( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 1000
        user.cash_account.save()
        user.save()

        cash_replenishment( 1000, user.cash_account )

        self.assertEqual( 2000, user.cash_account.amount )

class TestGeneralService( TestCase ):

    def test_generate_pin( self ):
        for _ in range( 999 ):
            pin = generate_pin()

            self.assertEqual( True, type(pin) == int )
            self.assertEqual( True, True if pin >= 1000 and pin <= 9999 else False )

    def test_CurrentCashAccount( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.save()

        current_cash_account = CurrentCashAccount()
        serializer = serializers.Serializer()

        serializer.context['request'] = PseudoRequest
        serializer.context['request'].user = user

        result = current_cash_account( serializer )

        self.assertEqual( True, isinstance( result, CashAccount ) )
        self.assertEqual( True, result == user.cash_account )

    def test_set_ignore_status_for_queryset( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.save()

        purchase = Purchase.objects.create( merchant = 'Art', amount = 100, cash_account = user.cash_account )

        self.assertEqual( False, purchase.is_ignore )
        set_ignore_status_for_queryset( True, user.cash_account.purchases.all() )
        self.assertEqual( True, Purchase.objects.get(pk = 1).is_ignore )

class TestCreditService( TestCase ):

    def test_calc_credit_amount_with_percent( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        self.assertEqual( 1515, calc_credit_amount_with_percent( credit ) )

        credit.is_increased_percentage = True
        credit.save()

        self.assertEqual( 1530, calc_credit_amount_with_percent( credit ) )
    
    def test_calc_remaining_amount_to_repay_credit( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        self.assertEqual( 1515, calc_remaining_amount_to_repay_credit( credit ) )

        credit.amount_returned = 200
        credit.is_increased_percentage = True
        credit.save()

        self.assertEqual( 1330, calc_remaining_amount_to_repay_credit( credit ) )

    def test_calc_amount_required_to_pay_one_credit_part( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )
        
        self.assertEqual( 505, calc_amount_required_to_pay_one_credit_part( credit ) )

        credit.is_increased_percentage = True
        credit.save()

        self.assertEqual( 510, calc_amount_required_to_pay_one_credit_part( credit ) )
    
    def test_calc_parts_remaining_to_pay_credit( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )
        
        self.assertEqual( 3, calc_parts_remaining_to_pay_credit( credit ) )

        credit.amount_returned = 580
        credit.save()

        self.assertEqual( 2, calc_parts_remaining_to_pay_credit( credit ) )
    
    def test_calc_number_paid_credit_parts( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )
        
        self.assertEqual( 0, calc_number_paid_credit_parts( credit ) )

        credit.amount_returned = 580
        credit.save()

        self.assertEqual( 1, calc_number_paid_credit_parts( credit ) )

    def test_calc_number_paid_credit_parts( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )
        
        self.assertEqual( 0, calc_number_paid_credit_parts( credit ) )

        credit.amount_returned = 580
        credit.save()

        self.assertEqual( 1, calc_number_paid_credit_parts( credit ) )
    
    def test_calc_payment_time_limit( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        key = next( i for i in settings.UNIT_PAYMENT_CREDIT_TIME.keys() )
        plus_to_credit_time = {
            key : 1
        }
            
        self.assertEqual( credit.last_payment_date + datetime.timedelta( **plus_to_credit_time ) , calc_payment_time_limit( credit ) )

        credit.amount_returned = 580
        credit.save()

        plus_to_credit_time = {
            key : 2
        }

        self.assertEqual( credit.last_payment_date + datetime.timedelta( **plus_to_credit_time ), calc_payment_time_limit( credit ) )

    def test_credit_repayment_check( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        self.assertEqual( False, credit_repayment_check( credit ) )

        credit.amount_returned = 1515
        credit.save()

        self.assertEqual( True, credit_repayment_check( credit ) )

    def test_payment_part_credit( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 505
        user.cash_account.save()
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        last_payment = credit.last_payment_date
        print('Wait one minute, for showing correct test result')
        sleep( 60 )
        self.assertEqual( True, payment_part_credit( credit, calc_amount_required_to_pay_one_credit_part(credit) ) )

        self.assertEqual( user.cash_account.amount, 0 )
        self.assertEqual( credit.amount_returned, 505 )
        self.assertEqual( 1, calc_number_paid_credit_parts( credit ) )
        self.assertEqual( True, credit.last_payment_date > last_payment )

        self.assertEqual( False, payment_part_credit( credit, calc_amount_required_to_pay_one_credit_part(credit) ) )

        last_payment = credit.last_payment_date

        self.assertEqual( user.cash_account.amount, 0 )
        self.assertEqual( credit.amount_returned, 505 )
        self.assertEqual( 1, calc_number_paid_credit_parts( credit ) )
        self.assertEqual( True, credit.last_payment_date == last_payment )
    
    def test_checking_payment_part_credit( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 505
        user.cash_account.save()
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        self.assertEqual( True, checking_payment_part_credit( credit ) )
        self.assertEqual( 1, user.cash_account.messages.count() )
        self.assertEqual( False, checking_payment_part_credit( credit ) )
        self.assertEqual( 2, user.cash_account.messages.count() )
    
    def test_checking_credits_status( self ):
        user = User.objects.create_user( email = 'mrloking11@gmail.com', first_name = 'Lo', last_name = 'ha', password = '123456' )
        user.cash_account.amount = 505
        user.cash_account.save()
        credit = Credit.objects.create( amount = 1500, loan_duration = 3, cash_account = user.cash_account )

        key = next( i for i in settings.UNIT_PAYMENT_CREDIT_TIME.keys() )
        plus_to_credit_time = {
            key : 1
        }
        credit.creation_date = credit.creation_date - datetime.timedelta( **plus_to_credit_time  )
        credit.save()

        checking_credits_status()

        self.assertEqual( 1, CashAccount.objects.get( user = user ).messages.count() )
        self.assertEqual( 0, CashAccount.objects.get( user = user ).amount )
        self.assertEqual( 505, Credit.objects.get( cash_account = user.cash_account ).amount_returned )
