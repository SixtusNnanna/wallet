class ExistsError(Exception):
    def __init__(self, name):
        self.name = name
        super().__init__(name)


class NotFoundError(Exception):
    def __init__(self, name):
        self.name = name
        super().__init__(name)

class InvalidPasswordError(Exception):
    pass

class InvalidTokenError(Exception):
    pass

class UserVerifyEmailError(Exception):
    pass

class PaymentInitiationError(Exception):
    pass

class NoActiveLoanError(Exception):
    pass

class RepaymentAlreadPendingError(Exception):
    pass

class PayStackError(Exception):
    pass

class IntegrityError(Exception):
    """ Websocket Already exist"""

class InvalidResponseError(Exception):
    pass

class PaymentError(Exception):
    pass
class PaymentAmountMismatchError(Exception):
    pass

class RepaymentAlreadyConfirmedError(Exception):
    pass

class BadRequestException(Exception):
    pass

class RepaymentAmountInsufficent(Exception):
    pass
