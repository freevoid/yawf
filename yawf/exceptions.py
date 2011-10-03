from coded_exceptions import CodedException


class YawfException(CodedException):
    pass


class WorkflowNotLoadedError(YawfException):
    pass


class WorkflowAlreadyRegisteredError(YawfException):
    pass


class OldStateInconsistenceError(YawfException):
    pass


class IllegalStateError(YawfException):
    pass


class UnhandledMessageError(YawfException):

    @property
    def context(self):
        return {'unhandled': self.args[0]}


class WrongHandlerResultError(YawfException):
    pass


class PermissionDeniedError(YawfException):
    pass


class ResourcePermissionDeniedError(PermissionDeniedError):
    pass


class MessageValidationError(YawfException):

    code = 'validation_error'
    @property
    def context(self):
        return self.args[0]


class CreateValidationError(MessageValidationError):
    pass


class MessageSpecNotRegisteredError(YawfException):
    pass


class GroupPathEmptyError(YawfException):
    pass


class MessageIgnored(YawfException):

    @property
    def context(self):
        return {"message_id": self.args[0], "message_params": self.args[1]}


class NoAvailableMessagesError(YawfException):
    pass


class ResourceNotFoundError(YawfException):
    pass


class ConcurrentRevisionUpdate(YawfException):
    pass
