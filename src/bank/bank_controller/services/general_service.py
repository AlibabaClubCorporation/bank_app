import random




def generate_pin() -> int:
    """
        Generates a pin code ( Number from 1000 to 9999 ) and returns it
    """

    return random.randint( 1000, 9999 )
