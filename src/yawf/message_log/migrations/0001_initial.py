# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MessageLog'
        db.create_table('message_log_messagelog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_logs_instance', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('initiator_content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='message_logs_initiator', null=True, to=orm['contenttypes.ContentType'])),
            ('initiator_object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True, null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('message_params', self.gf('django.db.models.fields.TextField')()),
            ('revision_before', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_message', null=True, to=orm['revision.Revision'])),
            ('revision_after', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pre_message', null=True, to=orm['revision.Revision'])),
        ))
        db.send_create_signal('message_log', ['MessageLog'])


    def backwards(self, orm):
        
        # Deleting model 'MessageLog'
        db.delete_table('message_log_messagelog')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initiator_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'message_logs_initiator'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'initiator_object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'message_params': ('django.db.models.fields.TextField', [], {}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'revision_after': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pre_message'", 'null': 'True', 'to': "orm['revision.Revision']"}),
            'revision_before': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'post_message'", 'null': 'True', 'to': "orm['revision.Revision']"})
        },
        'revision.revision': {
            'Meta': {'unique_together': "[('object_id', 'content_type', 'revision')]", 'object_name': 'Revision'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_log_record': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'affected_revisions'", 'null': 'True', 'to': "orm['message_log.MessageLog']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'revision': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'serialized_fields': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['message_log']
