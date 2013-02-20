# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Rscripts'
        db.create_table('breeze_rscripts', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=35)),
            ('inln', self.gf('django.db.models.fields.CharField')(max_length=75, blank=True)),
            ('details', self.gf('django.db.models.fields.CharField')(max_length=350, blank=True)),
            ('category', self.gf('django.db.models.fields.CharField')(default=u'general', max_length=25)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('draft', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('docxml', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('code', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('header', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('breeze', ['Rscripts'])

        # Adding model 'Jobs'
        db.create_table('breeze_jobs', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('jname', self.gf('django.db.models.fields.CharField')(max_length=55)),
            ('jdetails', self.gf('django.db.models.fields.CharField')(max_length=4900, blank=True)),
            ('juser', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('script', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['breeze.Rscripts'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('staged', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('progress', self.gf('django.db.models.fields.IntegerField')()),
            ('docxml', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('rexecut', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('breeze', ['Jobs'])

        # Adding model 'DataSet'
        db.create_table('breeze_dataset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=55)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=350, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('rdata', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('breeze', ['DataSet'])

        # Adding model 'InputTemplate'
        db.create_table('breeze_inputtemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=55)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=350, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('breeze', ['InputTemplate'])

        # Adding model 'UserProfile'
        db.create_table('breeze_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=35)),
            ('fimm_group', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('logo', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('breeze', ['UserProfile'])


    def backwards(self, orm):
        # Deleting model 'Rscripts'
        db.delete_table('breeze_rscripts')

        # Deleting model 'Jobs'
        db.delete_table('breeze_jobs')

        # Deleting model 'DataSet'
        db.delete_table('breeze_dataset')

        # Deleting model 'InputTemplate'
        db.delete_table('breeze_inputtemplate')

        # Deleting model 'UserProfile'
        db.delete_table('breeze_userprofile')


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
        'breeze.dataset': {
            'Meta': {'object_name': 'DataSet'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '350', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '55'}),
            'rdata': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'breeze.inputtemplate': {
            'Meta': {'object_name': 'InputTemplate'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '350', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '55'})
        },
        'breeze.jobs': {
            'Meta': {'object_name': 'Jobs'},
            'docxml': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jdetails': ('django.db.models.fields.CharField', [], {'max_length': '4900', 'blank': 'True'}),
            'jname': ('django.db.models.fields.CharField', [], {'max_length': '55'}),
            'juser': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'progress': ('django.db.models.fields.IntegerField', [], {}),
            'rexecut': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'script': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['breeze.Rscripts']"}),
            'staged': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'breeze.rscripts': {
            'Meta': {'ordering': "['name']", 'object_name': 'Rscripts'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'category': ('django.db.models.fields.CharField', [], {'default': "u'general'", 'max_length': '25'}),
            'code': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'details': ('django.db.models.fields.CharField', [], {'max_length': '350', 'blank': 'True'}),
            'docxml': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'draft': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'header': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inln': ('django.db.models.fields.CharField', [], {'max_length': '75', 'blank': 'True'}),
            'logo': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '35'})
        },
        'breeze.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'fimm_group': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '35'}),
            'logo': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['breeze']