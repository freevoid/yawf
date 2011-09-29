from yawf.exceptions import MessageValidationError
from django import forms

def clean_message_data(workflow, obj, message):
    message_spec = workflow.get_message_spec(message.id)
    validator_cls = message_spec.validator_cls
    if issubclass(validator_cls, forms.ModelForm):
        validator = validator_cls(message.raw_params, instance=obj)
    else:
        validator = validator_cls(message.raw_params)

    if validator.is_valid():
        message.params = message_spec.params_wrapper(validator.cleaned_data)
        # fix id in case it was a list (group path)
        message.id = message_spec.id
        message.spec = message_spec
    else:
        raise MessageValidationError(validator.errors)

    return message
