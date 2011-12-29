from yawf.exceptions import MessageValidationError

def clean_message_data(workflow, obj, message):
    message_spec = workflow.get_message_spec(message.id)

    if message.clean_params is None:
        validator_cls = message_spec.validator_cls
        validator = validator_cls(message.raw_params)

        if validator.is_valid():
            clean_params = validator.cleaned_data
        else:
            raise MessageValidationError(validator)
    else:
        clean_params = message.clean_params

    message.params = message_spec.params_wrapper(clean_params)
    # fix id in case it was a list (group path)
    message.id = message_spec.id
    message.spec = message_spec

    return message
