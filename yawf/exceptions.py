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

    code = 'yawf_validation_error'

    def __init__(self, validator):
        self.validator = validator

    @property
    def context(self):
        return self.validator.errors


class CreateValidationError(MessageValidationError):
    pass


class MessageSpecNotRegisteredError(YawfException):
    pass


class GroupPathEmptyError(YawfException):
    pass


class MessageIgnored(YawfException):

    @property
    def context(self):
        message = self.args[0]
        return {"message_id": message.id,
                "message_params": message.params}


class NoAvailableMessagesError(YawfException):
    pass


class ResourceNotFoundError(YawfException):
    pass


class ConcurrentRevisionUpdate(YawfException):
    pass
