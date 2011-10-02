from django.test import TestCase

import yawf
import yawf.creation
import yawf.dispatch

yawf.autodiscover()
from .models import Window


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

    def test_grouped_action(self):
        window, _ = self._new_window(width=500, height=300)
        self.assertEqual(window.width, 500)
        self.assertEqual(window.height, 300)

        resized_window, effects = yawf.dispatch.dispatch(window, self.sender,
            'edit__resize', dict(width=200, height=400))
        self.assertEqual(resized_window.width, 200)
        self.assertEqual(resized_window.height, 400)

        resized_window = Window.objects.get(id=window.id)
        self.assertEqual(resized_window.width, 200)
        self.assertEqual(resized_window.height, 400)

        self.assertListEqual(effects, ['edit_effect', 'resize_effect'])

    def _new_window(self, title='Main window', width=500, height=300):
        window = yawf.creation.create(
            self.workflow_id, self.sender,
            {
                'title': title,
                'width': width,
                'height': height,
            })
        return yawf.creation.start_workflow(window, self.sender)


class ViewTest(TestCase):

    def test_handlers_graph(self):
        response = self.client.get('/describe/simple/graph/handlers/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Type'))
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(len(response.content) > 1024)

    def test_effects_graph(self):
        response = self.client.get('/describe/simple/graph/effects/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Type'))
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(len(response.content) > 1024)
