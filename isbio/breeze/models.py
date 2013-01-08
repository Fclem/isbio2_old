from django.db import models
from django.template.defaultfilters import slugify
from django.core.files import File

CATEGORY_OPT = (
        (u'GEN', u'General'),
        (u'VIS', u'Visualization'),
        (u'RNA', u'Screening'),
        (u'SEQ', u'Sequencing'),
    )

class Rscripts(models.Model):
    name = models.CharField(max_length=15, unique=True)
    inln = models.CharField(max_length=75)
    details = models.CharField(max_length=350)
    categoty = models.CharField(max_length=3, choices=CATEGORY_OPT)

    def file_name(self, filename):
        fname, dot, extension = filename.rpartition('.')
        slug = slugify(self.name)
        return 'r_scripts/%s/%s.%s' % (slug, slug, extension)

    code = models.FileField(upload_to=file_name)
    docxml = models.FileField(upload_to=file_name)
    logo = models.FileField(upload_to=file_name)

    def __unicode__(self):
        return self.name


class Jobs(models.Model):
    pass

newrscript = Rscripts()
