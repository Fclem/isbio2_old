from django.db import models

class Data(models.Model):
    gene_name = models.CharField(max_length=15)
    dna_sequence = models.CharField(max_length=100)
    def __unicode__(self):
        return self.gene_name



class Rscript(models.Model):
    name = models.CharField(max_length=55)
    def __unicode__(self):
        return self.name

class User(models.Model):
    pass

class Job(models.Model):
    pass
