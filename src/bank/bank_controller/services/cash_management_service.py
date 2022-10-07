from bank_controller.models import CashAccount


def checking_availability_money( amount : int, account : CashAccount ) -> bool:
    """
        Returns True if the account has "amount" amount of money, and False otherwise
    """

    if amount > account.amount:
        return False
    
    return True

def cash_withdrawal( amount : int, account : CashAccount ) -> bool:
    """
        Tries to withdraw money from cash_account, if the operation is successful returns True, otherwise False
    """
    
    if not checking_availability_money( amount, account ):
        return False

    account.amount -= amount
    account.save()

    return True

def cash_replenishment( amount : int, account : CashAccount ) -> None:
    """
        Increases the amount of money in the given "account". Returns None
    """
    
    account.amount += amount
    account.save()