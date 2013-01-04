from django import forms
import xml.etree.ElementTree as xml
from breeze.models import CATEGORY_OPT
from bootstrap_toolkit.widgets import BootstrapTextInput, BootstrapUneditableInput

class NewForm(forms.Form):
    def setFields(self, kwds):
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

class ScriptGeneral(forms.Form):
    name = forms.CharField(
        max_length=15,
        help_text=u'Provide a short name for new script',
    )
    inln = forms.CharField(
        max_length=75,
        help_text=u'Inline Description',
    )
    category = forms.ChoiceField(
        choices=CATEGORY_OPT,
        help_text=u'Pick a category from the list',
    )
    logo = forms.FileField()
    details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 7}),
        help_text=u'More datailed description',
    )

class ScriptDetails(forms.Form):
    mark = forms.BooleanField(required=False)

class ScriptSource(forms.Form):
    code = forms.FileField()
    source = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 35, 'rows': 11}),
        help_text=u'Source code here',
    )

def xml_from_form(form):
    root = xml.Element('rScript')
    root.attrib['name'] = form.cleaned_data['name']
    child = xml.Element('inline')
    root.append(child)
    newxml = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml", 'w')
    xml.ElementTree(root).write(newxml)
    newxml.close()
    return newxml


def form_from_xml(xml):
    custom_form = NewForm()
    kwargs = dict()

    input_array = xml.getroot().find('inputArray')

    if input_array != None:
        for input_item in input_array:
            if input_item.tag == "inputItem":
                buid_item(input_item, kwargs)
            elif input_item.tag == "subSection":
                print "section"
            else:
                pass
    else:
        pass

    custom_form.setFields(kwargs)
    return custom_form

def buid_item(item, args):
    if  item.attrib["type"] == "num":  # numeric input
        args[item.attrib["comment"]] = forms.FloatField()

    elif item.attrib["type"] == "text":  # text box
        args[item.attrib["comment"]] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'type': 'text', })
                                                       )
    elif item.attrib["type"] == "textar":  # text area
        args[item.attrib["comment"]] = forms.CharField(
                widget=forms.Textarea(
                    attrs={
                        'cols': item.find('ncols').attrib['val'],
                        'rows': item.find('nrows').attrib['val']
                    }
                                      )
                                                       )

    elif item.attrib["type"] == "check":  # check box
        args[item.attrib["comment"]] = forms.BooleanField(required=False)

    elif item.attrib["type"] == "drop":  # drop down list
        drop_options = tuple()

        for alt in item.find('altArray').findall('altItem'):
            drop_options = drop_options + ((alt.text, alt.text),)

        args[item.attrib["comment"]] = forms.ChoiceField(choices=drop_options)

    elif item.attrib["type"] == "mult":  # multiple selection list
        mult_options = tuple()

        for alt in item.find('altArray').findall('altItem'):
            mult_options = mult_options + ((alt.text, alt.text),)

        args[item.attrib["comment"]] = forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple(
                    attrs={'inline': True, }
                                                    ),
                choices=(mult_options)
                                                                  )
    elif item.attrib["type"] == "radio":  # redio buttons
        radio_options = tuple()

        for alt in item.find('altArray').findall('altItem'):
            radio_options = radio_options + ((alt.text, alt.text),)

        args[item.attrib["comment"]] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'value': item.attrib["default"]}),
                choices=radio_options, help_text=u'',
                                                           )
    elif item.attrib["type"] == "file":  # file upload field
        args[item.attrib["comment"]] = forms.FileField()

    elif item.attrib["type"] == "heading":  # section header
        pass
    else:
        pass

