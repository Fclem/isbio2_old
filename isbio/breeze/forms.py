from django import forms

class DataForm(forms.Form):
    docfile = forms.FileField(label='Upload a data')
    plot = forms.ChoiceField(widget = forms.Select(), 
                     choices = ([('plot','Plot the data'), ('hisg','Distribution'),('box','Box Plot'), ]), 
			initial='1', required = True,label='What we do...?')
