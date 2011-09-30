from django.test import TestCase

import yawf
import yawf.creation
import yawf.dispatch

yawf.autodiscover()


class WorkflowTestMixin(object):

    workflow_id = None

    def get_workflow(self):
        return yawf.get_workflow(self.workflow_id)

    def test_workflow_registered(self):
        workflow = self.get_workflow()
        self.assertIsNotNone(workflow)

    def test_initial_handler(self):
        w = self.get_workflow()
        if isinstance(w.start_workflow, basestring):
            start_handler = w.get_handler(w.initial_state, w.start_workflow)
            self._test_handler_obj(start_handler)

    def test_initial_message(self):
        w = self.get_workflow()
        if isinstance(w.start_workflow, basestring):
            spec = w.get_message_spec(w.start_workflow)
            self._test_message_spec(spec)

    def _test_handler_obj(self, handler):
        self.assertIsInstance(handler, yawf.handlers.Handler)

    def _test_message_spec(self, spec):
        self.assertTrue(hasattr(spec, '__bases__'))
        self.assertIsInstance(spec, yawf.messages.spec.MessageSpecMeta)
        self.assertIsInstance(spec.id, basestring)
        self.assertTrue(hasattr(spec, 'validator_cls'))
        self.assertTrue(hasattr(spec.validator_cls, 'is_valid'))

    def test_validate(self):
        w = self.get_workflow()
        w.validate()


class SimpleWorkflowTest(TestCase, WorkflowTestMixin):

    workflow_id = 'simple'
    sender = '__sender__'

    def test_creation(self):

        self.assertRaises(
            yawf.exceptions.CreateValidationError,
            lambda: yawf.creation.create(self.workflow_id, self.sender, {}))

        window = yawf.creation.create(
            self.workflow_id, self.sender,
            {
                'title': 'Main window',
                'width': 500,
                'height': 300,
            })

        new_instance, side_effect = yawf.creation.start_workflow(window, self.sender)
        self.assertEqual(window.id, new_instance.id)
        self.assertFalse(window is new_instance)
