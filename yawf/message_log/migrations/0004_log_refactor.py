# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('reversion', '0005_auto__add_field_revision_manager_slug'),
    )

    def forwards(self, orm):
        
        # Deleting field 'MessageLog.parent_id'
        #db.delete_foreign_key('message_log_messagelog', 'parent_id_id')
        db.delete_column('message_log_messagelog', 'parent_id_id')

        # Deleting field 'MessageLog.revision_after'
        db.delete_foreign_key('message_log_messagelog', 'revision_after_id')
        db.delete_column('message_log_messagelog', 'revision_after_id')

        # Deleting field 'MessageLog.revision_before'
        db.delete_foreign_key('message_log_messagelog', 'revision_before_id')
        db.delete_column('message_log_messagelog', 'revision_before_id')

        # Adding field 'MessageLog.revision'
        db.add_column('message_log_messagelog', 'revision', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reversion.Revision'], null=True, blank=True), keep_default=False)

        # Adding field 'MessageLog.uuid'
        db.add_column('message_log_messagelog', 'uuid', self.gf('django.db.models.fields.CharField')(default='', max_length=36, db_index=True), keep_default=False)

        # Adding field 'MessageLog.parent_uuid'
        db.add_column('message_log_messagelog', 'parent_uuid', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=36, null=True, blank=True), keep_default=False)

        # Adding field 'MessageLog.group_uuid'
        db.add_column('message_log_messagelog', 'group_uuid', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=36, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'MessageLog.parent_id'
        db.add_column('message_log_messagelog', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['message_log.MessageLog'], null=True, blank=True), keep_default=False)

        # Adding field 'MessageLog.revision_after'
        db.add_column('message_log_messagelog', 'revision_after', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pre_message', null=True, to=orm['revision.Revision']), keep_default=False)

        # Adding field 'MessageLog.revision_before'
        db.add_column('message_log_messagelog', 'revision_before', self.gf('django.db.models.fields.related.ForeignKey')(related_name='post_message', null=True, to=orm['revision.Revision']), keep_default=False)

        # Deleting field 'MessageLog.revision'
        db.delete_foreign_key('message_log_messagelog', 'revision_id')
        db.delete_column('message_log_messagelog', 'revision_id')

        # Deleting field 'MessageLog.uuid'
        db.delete_column('message_log_messagelog', 'uuid')

        # Deleting field 'MessageLog.parent_uuid'
        db.delete_column('message_log_messagelog', 'parent_uuid')

        # Deleting field 'MessageLog.group_uuid'
        db.delete_column('message_log_messagelog', 'group_uuid')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
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
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent_uuid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '36', 'null': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reversion.Revision']", 'null': 'True', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '36', 'db_index': 'True'}),
            'workflow_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64', 'db_index': 'True'})
        },
        'reversion.revision': {
            'Meta': {'object_name': 'Revision'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manager_slug': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '200', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['message_log']
