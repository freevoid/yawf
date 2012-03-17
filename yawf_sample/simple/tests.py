from django.test import TestCase
import reversion

import yawf
import yawf.creation
import yawf.dispatch
from yawf.revision.utils import (
    diff_fields, versions_diff, deserialize_revision, previous_version)
from yawf.message_log.models import main_record_for_revision
from yawf.allowed import get_allowed

yawf.autodiscover()
from .models import Window, WINDOW_OPEN_STATUS


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
        new_instance, handler_effect, side_effect = yawf.creation.start_workflow(window, self.sender)
        self.assertEqual(window.id, new_instance.id)
        self.assertFalse(window is new_instance)

    def test_grouped_action(self):
        window, _, _ = self._new_window(width=500, height=300)
        self.assertEqual(window.width, 500)
        self.assertEqual(window.height, 300)

        resized_window, handler_effects, effects = yawf.dispatch.dispatch(window, self.sender,
            'edit__resize', dict(width=200, height=400))
        self.assertEqual(resized_window.width, 200)
        self.assertEqual(resized_window.height, 400)

        resized_window = Window.objects.get(id=window.id)
        self.assertEqual(resized_window.width, 200)
        self.assertEqual(resized_window.height, 400)

        self.assertListEqual(effects, ['edit_effect', 'resize_effect'])

    def test_multimessage(self):
        window, _, _ = self._new_window(width=500, height=300)
        child1, _, _ = self._new_window(parent=window)
        child2, _, _ = self._new_window(parent=window)

        window, handler_effects, _ = yawf.dispatch.dispatch(
                            window, self.sender, 'minimize_all')

        self.assertTrue(isinstance(handler_effects, list))
        self.assertEqual(len(handler_effects), 3)
        window, child1, child2 = handler_effects
        self.assertEqual(window.open_status, WINDOW_OPEN_STATUS.MINIMIZED)
        self.assertEqual(child1.open_status, WINDOW_OPEN_STATUS.MINIMIZED)
        self.assertEqual(child2.open_status, WINDOW_OPEN_STATUS.MINIMIZED)

    def test_revision_deserialization(self):
        window, _, _ = self._new_window(width=500, height=300)
        self.assertEqual(window.revision, 2)

        child1, _, _ = self._new_window(parent=window)
        child2, _, _ = self._new_window(parent=window)

        window, _, _ = yawf.dispatch.dispatch(
                            window, self.sender, 'minimize_all')

        versions = reversion.get_for_object(window)
        self.assertEqual(len(versions), 2)
        last_version = versions[0]
        message_revision = last_version.revision

        # checking log record
        log_record = main_record_for_revision(message_revision)
        self.assertEqual(log_record.message, 'minimize_all')
        self.assertEqual(log_record.object_id, window.id)

        # checking revision
        rev = deserialize_revision(message_revision)
        version = rev.get_version_for_record(log_record)
        self.assertEqual(last_version, version)
        previous = previous_version(version)
        diff = versions_diff(previous, version, full=True)
        self.assertItemsEqual(diff[0],
            {
                'field_name': 'open_status',
                'old': 'normal',
                'new': 'minimized',
                'field_verbose_name': 'open status'
            })
        self.assertItemsEqual(diff[1],
            {
                'field_name': 'revision',
                'old': '2',
                'new': '3',
                'field_verbose_name': 'revision'
            })

    def test_revision_diff(self):
        window, _, _ = self._new_window(width=500, height=300)
        self.assertEqual(window.revision, 2)

        resized_window, _, _ = yawf.dispatch.dispatch(window, self.sender,
            'edit__resize', dict(width=200, height=300))
        self.assertEqual(resized_window.revision, 3)

        versions = reversion.get_for_object(window)
        self.assertEqual(len(versions), 2)
        new_rev = versions[0]
        old_rev = versions[1]

        diff = list(diff_fields(old_rev, new_rev))
        self.assertItemsEqual(diff, ['width'])

        diff = versions_diff(old_rev, new_rev)
        self.assertItemsEqual(diff,
            [
                {
                    'field_name': 'width',
                    'old': 500,
                    'new': 200,
                    'field_verbose_name': 'width'
                },
            ])

    def test_allowed(self):
        window, _, _ = self._new_window()
        allowed = get_allowed(self.sender, window)
        self.assertItemsEqual(allowed.keys(), ['allowed_messages', 'allowed_resources'])


    def test_view_handling(self):
        window, _, _ = self._new_window(width=500, height=300)
        self.assertEqual(window.width, 500)
        self.assertEqual(window.height, 300)

        self.client.post(
            '/simple/window/%d/resize/' % window.id,
            {
                'width': 200,
                'height': 400,
            })

        window = Window.objects.get(pk=window.id)
        self.assertEqual(window.width, 200)
        self.assertEqual(window.height, 400)

        self.assertEqual(window.open_status, 'normal')
        r = self.client.post('/simple/window/%d/maximize/' % window.id)
        self.assertEqual(r.status_code, 200)

        window = Window.objects.get(pk=window.id)
        self.assertEqual(window.open_status, 'maximized')


    def _new_window(self, title='Main window', width=500, height=300,
            parent=None):
        window = yawf.creation.create(
            self.workflow_id, self.sender,
            {
                'title': title,
                'width': width,
                'height': height,
                'parent': parent.id if parent is not None else None,
            })
        return yawf.creation.start_workflow(window, self.sender)


class GraphViewTest(TestCase):

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
