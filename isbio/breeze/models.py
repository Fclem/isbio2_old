from django.db import models

class Data(models.Model):
    gene_name = models.CharField(max_length=15)
    dna_sequence = models.CharField(max_length=100)
    def __unicode__(self):
        return self.gene_name



