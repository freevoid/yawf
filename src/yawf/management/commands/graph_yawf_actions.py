from django.core.management.base import BaseCommand

from yawf import get_workflow
from yawf.graph import build_actions_graph


class Command(BaseCommand):

    def handle(self, workflow_id, **options):
        w = get_workflow(workflow_id)
        print build_actions_graph(w).to_string()
