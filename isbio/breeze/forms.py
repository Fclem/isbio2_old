from django import forms
from bootstrap_toolkit.widgets import BootstrapTextInput, BootstrapUneditableInput

class NewForm(forms.Form):
    def setFields(self, kwds):
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

class CreateScript(forms.Form):
    name = forms.CharField(
        max_length=15,
        help_text=u'Provide a short name for new script',
    )
    inln = forms.CharField(
        max_length=55,
        help_text=u'Inlihe Description',
    )
    details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 7}),
        help_text=u'More datailed description',
    )

class TestForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        help_text=u'This is the standard text input',
    )
    disabled = forms.CharField(
        max_length=100,
        help_text=u'I am disabled',
        widget=forms.TextInput(attrs={
            'disabled': 'disabled',
            'placeholder': 'I am disabled',
        })
    )
    uneditable = forms.CharField(
        max_length=100,
        help_text=u'I am uneditable and you cannot enable me with JS',
        initial=u'Uneditable',
        widget=BootstrapUneditableInput()
    )
    content = forms.ChoiceField(
        choices=(
            ("text", "Plain text"),
            ("html", "HTML"),
        ),
        help_text=u'Pick your choice',
    )
    email = forms.EmailField()
    like = forms.BooleanField(required=False)
    fruits = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ("apple", "Apple"),
            ("pear", "Pear"),
        ),
        help_text=u'As you can see, multiple checkboxes work too',
    )
    veggies = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={
            'inline': True,
        }),
        choices=(
            ("broccoli", "Broccoli"),
            ("carrots", "Carrots"),
            ("turnips", "Turnips"),
        ),
        help_text=u'And can be inline',
    )
    color = forms.ChoiceField(
        widget=forms.RadioSelect(attrs={'data-demo-attr': 'bazinga' }),
        choices=(
            ("#f00", "red"),
            ("#0f0", "green"),
            ("#00f", "blue"),
        ),
        help_text=u'And we have <i>radiosets</i>',
    )
    prepended = forms.CharField(
        max_length=100,
        help_text=u'I am prepended by a P',
        widget=BootstrapTextInput(prepend='P'),
    )

    def clean(self):
        cleaned_data = super(TestForm, self).clean()
        raise forms.ValidationError("This error was added to show the non field errors styling.")
        return cleaned_data

def generate_form(xml):
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

