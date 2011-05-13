from yawf.exceptions import MessageValidationError


def clean_message_data(workflow, obj, message):
    message_spec = workflow.get_message_spec(message.id)
    validator_cls = message_spec.validator_cls
    validator = validator_cls(message.raw_params)

    if validator.is_valid():
        message.params = message_spec.params_wrapper(validator.cleaned_data)
    else:
        raise MessageValidationError(validator.errors)

    return message
