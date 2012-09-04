# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'MessageLog.revision_content_type'
        db.add_column('message_log_messagelog', 'revision_content_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='message_logs_revision', null=True, to=orm['contenttypes.ContentType']),
                      keep_default=False)

        # Adding field 'MessageLog.revision_id'
        db.alter_column('message_log_messagelog', 'revision_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True),
                      explicit_name=True)


    def backwards(self, orm):
        # Adding field 'MessageLog.revision'
        db.alter_column('message_log_messagelog', 'revision_id',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_log', null=True, to=orm['reversion.Revision'], blank=True),
                      explicit_name=True)

        # Deleting field 'MessageLog.revision_content_type'
        db.delete_column('message_log_messagelog', 'revision_content_type_id')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'message_log.messagelog': {
            'Meta': {'ordering': "('created_at',)", 'object_name': 'MessageLog'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_logs_instance'", 'to': "orm['contenttypes.ContentType']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'group_uuid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initiator_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'message_logs_initiator'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'initiator_object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'message_params': ('django.db.models.fields.TextField', [], {}),
            'message_params_dehydrated': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent_uuid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'revision_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'message_logs_revision'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'revision_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'transition_result': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'db_index': 'True'}),
            'workflow_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'db_index': 'True'})
        }
    }

    complete_apps = ['message_log']
