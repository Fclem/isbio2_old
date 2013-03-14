from django import forms
from django.conf import settings
import xml.etree.ElementTree as xml
import breeze.models
from django.contrib.auth.models import User
# from bootstrap_toolkit.widgets import BootstrapTextInput, BootstrapPasswordInput


class RegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(forms.ModelForm, self).__init__(*args, **kw)
        self.fields.keyOrder = [
            'username',
            'email',
            'first_name',
            'last_name',
            'fimm_group',
            'password',
            'password1']

    username = forms.CharField(label=(u'User Name'))
    email = forms.EmailField(label=(u'Email Address'))
    password = forms.CharField(label=(u'Password'), widget=forms.PasswordInput(render_value=False))
    password1 = forms.CharField(label=(u'Verify Password'), widget=forms.PasswordInput(render_value=False))

    class Meta:
        model = breeze.models.UserProfile
        exclude = ('user', 'logo')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        else:
            raise forms.ValidationError("That user name is already taken.")

    def clean(self):
        password = self.cleaned_data.get('password', None)
        password1 = self.cleaned_data.get('password1', None)
        if password and password1 and (password == password1):
            return self.cleaned_data
        else:
            raise forms.ValidationError("The passowords did not match. Please try again.")


class LoginForm(forms.Form):
    user_name = forms.CharField(
        max_length=30,
        label="",
        widget=forms.TextInput(
             attrs={
             'placeholder': 'user name...',
             'class': 'input-medium',
         }),
    )
    password = forms.CharField(
        max_length=30,
        label="",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'password...',
            'class': 'input-small',
        })
    )

class NewScriptDialog(forms.Form):
    name = forms.CharField(label=(u'Script Name'))

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            breeze.models.Rscripts.objects.get(name=name)
        except breeze.models.Rscripts.DoesNotExist:
            return name
        else:
            raise forms.ValidationError("That script name is already taken.")


class BasicJobForm(forms.Form):
    def __init__(self, user, edit, *args, **kwargs):
        self._user = user
        self._edit = edit
        super(BasicJobForm, self).__init__(*args, **kwargs)

    job_name = forms.CharField(
        max_length=35,
    )
    job_details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 3, 'placeholder': 'optional'}),
        required=False
    )

    def clean_job_name(self):
        job_name = self.cleaned_data.get('job_name')
        try:
            exst = breeze.models.Jobs.objects.filter(juser__exact=self._user).get(jname=job_name)
        except breeze.models.Jobs.DoesNotExist:
            return job_name
        else:
            if str(exst) == str(self._edit):
                return job_name
            else:
                raise forms.ValidationError("That job name already exists.")

class CustomForm(forms.Form):
    def setFields(self, kwds):
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

### Forms for script submissions ###
class ScriptBasics(forms.Form):
    name = forms.CharField(
        max_length=35,
        widget=forms.TextInput(
             attrs={
                'class': 'input-large',
         }),
    )
    inline = forms.CharField(
        max_length=150,
        label="Inline Description",
        widget=forms.Textarea(
             attrs={
                'class': 'input-xxlarge',
                'rows': 3
         }),
    )

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            exst = breeze.models.Rscripts.objects.get(name=name)
        except breeze.models.Rscripts.DoesNotExist:
            return name
        else:
            if str(exst) == str(name):
                return name
            else:
                raise forms.ValidationError("That script name is already taken.")

class ScriptDescription(forms.Form):
    description = forms.CharField(
        max_length=5500,
        label="",
        widget=forms.Textarea(
             attrs={
                'class': 'input-xxlarge',
                'rows': 11
         }),
    )

class ScriptAttributes(forms.ModelForm):
    class Meta:
        model = breeze.models.Rscripts
        fields = ('category', 'author', 'draft')

class ScriptLogo(forms.Form):
    logo = forms.FileField(label=(u''))

### old implementation ###
class ScriptMainForm(forms.ModelForm):
    class Meta:
        model = breeze.models.Rscripts
        fields = ('name', 'inln', 'category', 'details', 'logo')

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
#    default = forms.CharField(max_length=35,
#        widget=forms.TextInput(attrs={'class': 'input-mini'}),
#        required=False
#        )

class AddOptions(forms.Form):
    def drop_titles(self, *args, **kwargs):
        self.fields['options'].label = ""

    options = forms.CharField(max_length=55,
        widget=forms.TextInput(attrs={'class': 'input-xlarge'}))

class AddDatasetSelect(forms.Form):
    options = forms.ModelMultipleChoiceField(queryset=breeze.models.DataSet.objects.all(), widget=forms.CheckboxSelectMultiple())

class AddTemplateInput(forms.Form):
    """ 
        This control is for uploading template
        inpit file which can be downloaded from BREEZE beforehand 
    """
    options = forms.ModelChoiceField(queryset=breeze.models.InputTemplate.objects.all())

class HiddenForm(forms.Form):
    next = forms.CharField(widget=forms.HiddenInput())
    curr = forms.CharField(widget=forms.HiddenInput())


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
        common_form = form_d[key][0]
        ipt = xml.Element('inputItem')
        ipt.attrib['type'] = common_form.cleaned_data['type']
        ipt.attrib['rvarname'] = common_form.cleaned_data['inline_var']
        ipt.attrib['comment'] = common_form.cleaned_data['comment']
        ipt.attrib['val'] = ""

        if common_form.cleaned_data['type'] == 'TPL':
            extra_form = form_d[key][1]
            ipt.attrib['default'] = str(extra_form.cleaned_data['options'])
        else:
            ipt.attrib['default'] = ""

        if common_form.cleaned_data['type'] == 'DRP' or common_form.cleaned_data['type'] == 'RAD':
            extra_form = form_d[key][1]  # [0] form is the common one
            altar = xml.Element('altArray')
            for opt in str(extra_form.cleaned_data['options']).split():
                altit = xml.Element('altItem')
                altit.text = opt
                altar.append(altit)
            ipt.append(altar)

        if common_form.cleaned_data['type'] == 'DTS':
            extra_form = form_d[key][1]
            altar = xml.Element('altArray')
            for opt in extra_form.cleaned_data['options']:
                altit = xml.Element('altItem')
                altit.text = str(opt)
                altar.append(altit)
            ipt.append(altar)

        input_array.append(ipt)

    root.append(input_array)

    # newxml = open("/home/comrade/Projects/fimm/tmp/test.xml", 'w')
    newxml = open(str(settings.TEMP_FOLDER) + 'test.xml', 'w')
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

                elif input_item.attrib["type"] == "DTS":  # custom dataset (drop down list control)
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
                elif input_item.attrib["type"] == "FIL" or input_item.attrib["type"] == "TPL":  # file upload field
                    custom_form.fields[input_item.attrib["comment"]] = forms.FileField(
                            # initial=input_item.attrib["val"],
                            widget=forms.ClearableFileInput(
                                attrs={
                                       'class': input_item.attrib["type"],
                                       'which': input_item.attrib["default"],
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

def job_summary(xml):
    pass
