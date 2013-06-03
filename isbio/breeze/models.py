from django.db import models
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User


CATEGORY_OPT = (
        (u'general', u'General'),
        (u'visualization', u'Visualization'),
        (u'screening', u'Screening'),
        (u'sequencing', u'Sequencing'),
    )

class ReportType(models.Model):
    type = models.CharField(max_length=17)
    description = models.CharField(max_length=350, blank=True)
    search = models.BooleanField(default=True)
    # tags = models.ManyToManyField(Rscripts, blank=True)

    def __unicode__(self):
        return self.type

    class Meta:
        ordering = ('type',)

class Rscripts(models.Model):
    name = models.CharField(max_length=35, unique=True)
    inln = models.CharField(max_length=150, blank=True)
    details = models.CharField(max_length=5500, blank=True)
    category = models.CharField(max_length=25, choices=CATEGORY_OPT, default=u'general')
    author = ForeignKey(User)
    creation_date = models.DateField(auto_now_add=True)
    draft = models.BooleanField(default=True)
    istag = models.BooleanField(default=False)
    must = models.BooleanField(default=False)  # defines wheather the tag is enabled by default
    report_type = models.ForeignKey(ReportType, null=True, blank=True, default=None)  # assosiation with report type

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.name)
        return 'scripts/%s/%s.%s' % (slug, slug, extension)

    docxml = models.FileField(upload_to=file_name, blank=True)
    code = models.FileField(upload_to=file_name, blank=True)
    header = models.FileField(upload_to=file_name, blank=True)
    logo = models.FileField(upload_to=file_name, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Jobs(models.Model):
    jname = models.CharField(max_length=55)
    jdetails = models.CharField(max_length=4900, blank=True)
    juser = ForeignKey(User)
    script = ForeignKey(Rscripts)
    # status may be changed to NUMVER later
    status = models.CharField(max_length=15)
    staged = models.DateField(auto_now_add=True)
    progress = models.IntegerField()
    sgeid = models.CharField(max_length=15, blank=True)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.jname + '_' + self.juser.username)
        return 'jobs/%s/%s.%s' % (slug, slug, extension)

    docxml = models.FileField(upload_to=file_name)
    rexecut = models.FileField(upload_to=file_name)

    def __unicode__(self):
        return self.jname

class DataSet(models.Model):
    name = models.CharField(max_length=55, unique=True)
    description = models.CharField(max_length=350, blank=True)
    author = ForeignKey(User)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.name)
        return 'datasets/%s.%s' % (slug, extension)

    rdata = models.FileField(upload_to=file_name)

    def __unicode__(self):
        return self.name

class InputTemplate(models.Model):
    name = models.CharField(max_length=55, unique=True)
    description = models.CharField(max_length=350, blank=True)
    author = ForeignKey(User)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.name)
        return 'mould/%s.%s' % (slug, extension)

    file = models.FileField(upload_to=file_name)

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.name)
        return 'profiles/%s/%s.%s' % (slug, slug, extension)

    fimm_group = models.CharField(max_length=75)
    logo = models.FileField(upload_to=file_name, blank=True)

    def __unicode__(self):
        return self.first_name

class Report(models.Model):
    type = models.ForeignKey(ReportType)
    name = models.CharField(max_length=55)
    description = models.CharField(max_length=350, blank=True)
    author = ForeignKey(User)
    created = models.DateField(auto_now_add=True)
    home = models.CharField(max_length=155, blank=True)
    status = models.CharField(max_length=15, blank=True)
    sgeid = models.CharField(max_length=15)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(str(self.id) + '_' + self.name + '_' + self.author.username)
        return 'reports/%s/%s' % (slug, filename)

    rexec = models.FileField(upload_to=file_name, blank=True)
    dochtml = models.FileField(upload_to=file_name, blank=True)

    def __unicode__(self):
        return self.name
