from django import forms
import re
from django.forms.formsets import formset_factory, BaseFormSet
import xml.etree.ElementTree as xml
from breeze.models import CATEGORY_OPT
from bootstrap_toolkit.widgets import BootstrapTextInput, BootstrapUneditableInput

class BasicJobForm(forms.Form):
    job_name = forms.CharField(
        max_length=35,
    )
    job_details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 7}),
        help_text=u'(optional)',
        required=False
    )

class CustomForm(forms.Form):
    def setFields(self, kwds):
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

class ScriptGeneral(forms.Form):
    name = forms.CharField(
        max_length=35,
        help_text=u'Short name for new script',
    )
    inln = forms.CharField(
        max_length=95,
        help_text=u'Inline Description',
    )
    category = forms.ChoiceField(
        choices=CATEGORY_OPT,
        help_text=u'Pick a category from the list',
    )
    # logo = forms.FileField(required=False)
    details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 7}),
        help_text=u'More datailed description',
    )

class ScriptSources(forms.Form):
    code = forms.FileField()
    header = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 55, 'rows': 15, }),
        help_text='Header',
    )

class AddBasic(forms.Form):
    TYPE_OPT = (
        (u'NUM', u'Numeric'),
        (u'CHB', u'Check Box'),
        (u'DRP', u'Drop Down'),
        (u'RAD', u'Radio'),
        (u'TEX', u'Text'),
        (u'TAR', u'Text Area'),
        (u'FIL', u'File Upload'),
        (u'HED', u'Heading'),
    )

    def drop_titles(self, *args, **kwargs):
        self.fields['inline_var'].label = ""
        self.fields['comment'].label = ""

    inline_var = forms.CharField(max_length=35,
        widget=forms.TextInput(attrs={'class': 'input-mini'})
        )
    type = forms.CharField(widget=forms.HiddenInput(), required=False)
    comment = forms.CharField(max_length=55,
        widget=forms.TextInput(attrs={'class': 'input-xlarge'})
        )
    default = forms.CharField(max_length=35,
        widget=forms.TextInput(attrs={'class': 'input-mini'}),
        required=False
        )

class AddOptions(forms.Form):
    def drop_titles(self, *args, **kwargs):
        self.fields['options'].label = ""

    options = forms.CharField(max_length=55,
        widget=forms.TextInput(attrs={'class': 'input-xlarge'}))

class HiddenForm(forms.Form):
    next = forms.CharField(widget=forms.HiddenInput())
    curr = forms.CharField(widget=forms.HiddenInput())

def get_job_xml(tree, data, code, header):
    rexec = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/rexec.r", 'w')
    script_header = open("/home/comrade/Projects/fimm/isbio/breeze/" + str(header), "rb").read()
    script_code = open("/home/comrade/Projects/fimm/isbio/breeze/" + str(code), "rb").read()

    params = ''
    for item in tree.getroot().iter('inputItem'):
        item.set('val', str(data.cleaned_data[item.attrib['comment']]))
        if item.attrib['type'] == 'CHB':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]).upper() + '\n'
        elif item.attrib['type'] == 'NUM':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]) + '\n'
        elif item.attrib['type'] == 'TAR':
            lst = re.split(', |,|\n|\r| ', str(data.cleaned_data[item.attrib['comment']]))
            seq = 'c('
            for itm in lst:
                if itm != "":
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        else:  # for text, text_are, drop_down, radio and file
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'

    tree.write('/home/comrade/Projects/fimm/isbio/breeze/tmp/job.xml')

    rexec.write("#####################################\n")
    rexec.write("###       Code Section            ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_code)
    rexec.write("\n\n#####################################\n")
    rexec.write("### Parameters Definition Section ###\n")
    rexec.write("#####################################\n")
    rexec.write(params)
    rexec.write("\n\n#####################################\n")
    rexec.write("###       Assembly Section        ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_header)

    rexec.close()
    return 1

def build_header(data):
    header = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/header.txt", 'w')
    string = str(data)
    header.write(string)
    header.close()
    return header


def xml_from_form(form_g, form_d, form_s):
    root = xml.Element('rScript')
    root.attrib['name'] = form_g.cleaned_data['name']
    inline = xml.Element('inline')
    inline.text = form_g.cleaned_data['inln']
    root.append(inline)
    details = xml.Element('details')
    details.text = form_g.cleaned_data['details']
    root.append(details)
    status = xml.Element('status')
    status.attrib['val'] = 'none'
    root.append(status)
    input_array = xml.Element('inputArray')

    for key in form_d:
        form = form_d[key][0]
        ipt = xml.Element('inputItem')
        ipt.attrib['type'] = form.cleaned_data['type']
        ipt.attrib['rvarname'] = form.cleaned_data['inline_var']
        ipt.attrib['default'] = form.cleaned_data['default']
        ipt.attrib['comment'] = form.cleaned_data['comment']
        ipt.attrib['val'] = ""
        # ipt.attrib['val'] = ""

        if form.cleaned_data['type'] == 'DRP' or form.cleaned_data['type'] == 'RAD':
            form = form_d[key][1]
            altar = xml.Element('altArray')
            for opt in str(form.cleaned_data['options']).split():
                altit = xml.Element('altItem')
                altit.text = opt
                altar.append(altit)
            ipt.append(altar)
        input_array.append(ipt)

    root.append(input_array)

    newxml = open("/home/comrade/Projects/fimm/isbio/breeze/tmp/test.xml", 'w')
    xml.ElementTree(root).write(newxml)
    newxml.close()
    return newxml

def form_from_xml(xml, req=None, init=False):
    input_array = xml.getroot().find('inputArray')

    if req:
        custom_form = CustomForm(req.POST, req.FILES)
    elif init:
        custom_form = CustomForm(req.POST, req.FILES)
    else:
        custom_form = CustomForm()


    if input_array != None:
        for input_item in input_array:
            print "1"
            if input_item.tag == "inputItem":
                if  input_item.attrib["type"] == "NUM":  # numeric input
                    custom_form.fields[input_item.attrib["comment"]] = forms.FloatField(initial=input_item.attrib["val"])

                elif input_item.attrib["type"] == "TEX":  # text box
                    custom_form.fields[input_item.attrib["comment"]] = forms.CharField(
                            initial=input_item.attrib["val"],
                            max_length=100,
                            widget=forms.TextInput(attrs={'type': 'text', })
                                                                   )
                elif input_item.attrib["type"] == "TAR":  # text area
                    custom_form.fields[input_item.attrib["comment"]] = forms.CharField(
                            initial=input_item.attrib["val"],
                            widget=forms.Textarea(
                                attrs={
                                    'cols': 15,
                                    'rows': 3,
                                }
                                                  )
                                                                   )

                elif input_item.attrib["type"] == "CHB":  # check box
                    custom_form.fields[input_item.attrib["comment"]] = forms.BooleanField(required=False, initial=input_item.attrib["val"])

                elif input_item.attrib["type"] == "DRP":  # drop down list
                    drop_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        drop_options = drop_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.ChoiceField(choices=drop_options, initial=input_item.attrib["val"])

                elif input_item.attrib["type"] == "RAD":  # radio buttons
                    radio_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        radio_options = radio_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.ChoiceField(
                            initial=input_item.attrib["val"],
                            widget=forms.RadioSelect(attrs={'value': input_item.attrib["default"]}),
                            choices=radio_options, help_text=u'',
                                                                       )
                elif input_item.attrib["type"] == "FIL":  # file upload field
                    custom_form.fields[input_item.attrib["comment"]] = forms.FileField(
                            initial=input_item.attrib["val"],
                            widget=forms.ClearableFileInput(
                                attrs={
                                       'class': "fileup",
                                }
                                                            )
                                                                                       )

                elif input_item.attrib["type"] == "HED":  # section header
                    pass
                else:
                    pass
            elif input_item.tag == "subSection":
                print "section"
            else:
                pass


    return custom_form


def form_from_xml_old(xml):
    custom_form = CustomForm()
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
    if  item.attrib["type"] == "NUM":  # numeric input
        args[item.attrib["comment"]] = forms.FloatField()

    elif item.attrib["type"] == "TEX":  # text box
        args[item.attrib["comment"]] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={'type': 'text', })
                                                       )
    elif item.attrib["type"] == "TAR":  # text area
        args[item.attrib["comment"]] = forms.CharField(
                widget=forms.Textarea(
                    attrs={
                        'cols': item.find('ncols').attrib['val'],
                        'rows': item.find('nrows').attrib['val']
                    }
                                      )
                                                       )

    elif item.attrib["type"] == "CHB":  # check box
        args[item.attrib["comment"]] = forms.BooleanField(required=False)

    elif item.attrib["type"] == "DRP":  # drop down list
        drop_options = tuple()

        for alt in item.find('altArray').findall('altItem'):
            drop_options = drop_options + ((alt.text, alt.text),)

        args[item.attrib["comment"]] = forms.ChoiceField(choices=drop_options)

    elif item.attrib["type"] == "RAD":  # radio buttons
        radio_options = tuple()

        for alt in item.find('altArray').findall('altItem'):
            radio_options = radio_options + ((alt.text, alt.text),)

        args[item.attrib["comment"]] = forms.ChoiceField(
                widget=forms.RadioSelect(attrs={'value': item.attrib["default"]}),
                choices=radio_options, help_text=u'',
                                                           )
    elif item.attrib["type"] == "FIL":  # file upload field
        args[item.attrib["comment"]] = forms.FileField()

    elif item.attrib["type"] == "HED":  # section header
        pass
    else:
        pass




