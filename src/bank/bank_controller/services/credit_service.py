import datetime
from math import ceil

from django.conf import settings

from bank_controller.models import *
from bank_controller.services.general_service import *
from bank_controller.services.cash_management_service import *



def calc_credit_amount_with_percent( obj : Credit ) -> int:
    """
        Returns the credit amount including percents
    """

    amount = obj.amount
    percent = 1 + int( obj.is_increased_percentage )

    return amount + ( amount / 100 ) * percent

def calc_remaining_amount_to_repay_credit( obj : Credit ) -> int:
    """
        Returns the amount required to fully repay the credit
    """

    return calc_credit_amount_with_percent( obj ) - obj.amount_returned

def calc_amount_required_to_pay_one_credit_part( obj : Credit ) -> int:
    """
        Returns the amount required to pay one ( next ) part of the credit
    """

    amount_to_pay_one_part = calc_credit_amount_with_percent( obj ) / obj.loan_duration
    amount_to_fully_repay = calc_remaining_amount_to_repay_credit( obj )

    if amount_to_fully_repay > amount_to_pay_one_part:
        return amount_to_pay_one_part
    
    return amount_to_fully_repay
    
def calc_parts_remaining_to_pay_credit( obj : Credit ) -> int:
    """
        Returns the number of installments left to fully repay the credit
    """

    return ceil( calc_remaining_amount_to_repay_credit( obj ) / calc_amount_required_to_pay_one_credit_part( obj ) )

def calc_number_paid_credit_parts( obj : Credit ) -> int:
    """
        Return the number of paid installments of the credit
    """

    return obj.loan_duration - calc_parts_remaining_to_pay_credit( obj )

def calc_payment_time_limit( obj : Credit ) -> datetime.timedelta:
    """
        Returns the time until the next payment
    """

    amount_paid_parts_credit = calc_number_paid_credit_parts( obj )

    key = next( i for i in settings.UNIT_PAYMENT_CREDIT_TIME.keys() )
    plus_to_credit_time = {
        key : amount_paid_parts_credit + int( obj.is_increased_percentage ) + 1
    }
    
    return obj.creation_date + datetime.timedelta( **plus_to_credit_time )



def credit_repayment_check( credit : Credit ) -> None:
    """
        Removes a loan if it has been paid
    """

    if calc_credit_amount_with_percent( credit ) == credit.amount_returned:
        credit.delete()
        return True
    
    return False

def payment_part_credit( credit : Credit, amount : int ) -> bool:
    """
        Withdraws money for part of the credit, returns True if successful, False otherwise
    """

    # If the specified amount for payment is greater than the amount required to pay the loan, the amount will be equal to the amount required to pay the loan
    amount_required_to_repay_credit = calc_remaining_amount_to_repay_credit( credit )
    if amount > amount_required_to_repay_credit:
        amount = amount_required_to_repay_credit
        
    # If the money was withdrawn
    if cash_withdrawal( amount, credit.cash_account ):
        # The result is the total amount repaid for this loan
        credit.amount_returned += amount
        credit.save()

        # Update the date of the last payment
        credit.last_payment_date = datetime.datetime.now( tz = settings.TIME_ZONE_DATETIME_MODULE_FORMAT )
        credit.save()

        # Creates a purchase object, with the merchant specified as the credit part of which was paid
        Purchase.objects.create(
            cash_account = credit.cash_account,
            amount = amount,
            merchant = f'Credit | PK: {credit.pk}',
        )

        # Removes blocking from the account if it had non-payments before
        credit.cash_account.is_blocked = False
        credit.cash_account.save()
        
        # Creates a message notifying about the payment of a part of the loan
        message_content = f'Your account has been debited for part of the credit'
        Message.objects.create( cash_account = credit.cash_account, content = message_content )
        
        # If the loan is paid in full, deletes the record and sends a message
        credit_repayment_check( credit )

        return True

    return False

def checking_payment_part_credit( credit : Credit ) -> bool:
    """
        Checks the payment status of a portion of a loan.
        If the operation is successful:
        - Sends a message about successful payment.
        - If the user has been blocked - unblocks him.
        If the operation is not successful:
        - Sends the required message
        - Increases the percentage of the loan rate for the first non-payment of the loan part
        - Blocks the user for a second or more non-payment of the loan
    """

    # Specifies the amount to be paid. If the user is already blocked due to non-payment of the loan,
    # then according to the rules of the bank, the amount to be paid is the full amount to pay the loan
    if not credit.cash_account.is_blocked:
        payment_amount = calc_amount_required_to_pay_one_credit_part( credit )
    else:
        payment_amount = calc_remaining_amount_to_repay_credit( credit )

    # Tries to pay off part/all of a loan
    if not payment_part_credit( credit, payment_amount ):
        # If the payment is not successful and the interest has not yet been increased, the interest rate of the loan is raised
        if not credit.is_increased_percentage:
            credit.is_increased_percentage = True
            credit.save()
            message_content = f'Due to non-payment of the credit, the interest rate was increased for the credit with the identifier "{credit.pk}"'
            Message.objects.create( cash_account =  credit.cash_account, content = message_content )
        # If the interest has already been increased, which means that the user has not paid the loan,
        # the user account is blocked according to the rules of the bank's credit system
        else:
            if not credit.cash_account.is_blocked:
                credit.cash_account.is_blocked = True
                credit.cash_account.save()

                message_content = f'Your account is blocked due to non-payment of the credit. To unlock the account, you need to invest the amount ( { calc_remaining_amount_to_repay_credit(credit) } ), after withdrawing the money, the account will be unlocked'
                Message.objects.create( cash_account =  credit.cash_account, content = message_content )
        
        return False

    return True

def checking_credits_status() -> None:
    """
        Checks all existing credits.
        Sends a message and increases the percentage if the credit is not paid on time.
        Blocks the debtor's account if the credit has not been paid twice.
        Withdraws money from the account if it is enough to repay the necessary part of the credit.
    """

    # Collection of all credits
    credits = Credit.objects.all().select_related( 'cash_account' )

    # Go through all the credit to check
    for credit in credits:
        # Calculates the time to make the next payment

        payment_time_limit = calc_payment_time_limit( credit )

        # The condition will return True when it is necessary to repay part of the credit
        if payment_time_limit < datetime.datetime.now( tz = settings.TIME_ZONE_DATETIME_MODULE_FORMAT ):
            checking_payment_part_credit(credit)