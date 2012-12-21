# -*- coding: utf-8 -*-

from django.template import Template, Context
from django.template.context import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from breeze.models import Rscript
from bootstrap_toolkit.widgets import BootstrapUneditableInput

from xml.dom import minidom
from forms import TestForm, NewForm
from django import forms

from rpy2.robjects import r

def base(request):
    return render_to_response('base.html')

def login(request):
    return render_to_response('login.html')

def breeze(request):
    return render_to_response('index.html')

def home(request):
    return render_to_response('home.html', {})

def scripts(request):
    all_scripts = Rscript.objects.order_by("name")
    return render_to_response('scripts.html', {'script_list': all_scripts})

def jobs(request):
    return render_to_response('jobs.html', {})

def demo_form(request):
    layout = request.GET.get('layout')
    if not layout:
        layout = 'horizontal'
    if request.method == 'POST':
        form = TestForm(request.POST)
        form.is_valid()
    else:
        form = TestForm()
    form.fields['title'].widget = BootstrapUneditableInput()
    return render_to_response('forms/base_form.html', RequestContext(request, {
        'form': form,
        'layout': layout,
    }))

def read_form(request):
    dom = minidom.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')
    script_name = dom.getElementsByTagName("rScript")[0].getAttribute("name")
    node = dom.getElementsByTagName("inline")[0]
    script_inline = getText(node.childNodes)
    form = generateForm(dom)
    return render_to_response('forms/base_form.html', RequestContext(request, {
        'form': form,
        'name': script_name,
        'inline': script_inline,
        'layout': "horizontal",
    }))

# Of course it is temporary here...
def generateForm(xml):
    custom_form = NewForm()
    kwargs = dict()
    inputItems = xml.childNodes[0].getElementsByTagName("inputItem")

    for item in inputItems:
        if  item.getAttribute("type") == "num":
            kwargs[item.getAttribute("comment")] = forms.CharField(max_length=100,
                widget=forms.TextInput(attrs={
                    'type': 'number',
                    # 'placeholder': 'Should be text...',
                    'min': "1",
                    'max': "5",
                    'value': item.getAttribute("default"),
            }))
            custom_form.setFields(kwargs)
        elif item.getAttribute("type") == "text":
            kwargs[item.getAttribute("comment")] = forms.CharField(max_length=100,
                widget=forms.TextInput(attrs={
                    'type': 'text',
                     'placeholder': 'We can put some text like that...',
            }))
        elif item.getAttribute("type") == "textar":
            pass
        elif item.getAttribute("type") == "check":
            pass
        elif item.getAttribute("type") == "drop":
            drop_options = tuple()
            alt = item.childNodes
            for j in alt:
                opt = j.childNodes
                for k in opt:
                    if len(getText(j.childNodes)) == 0 :
                        pass
                    else:
                        drop_options = drop_options + ((getText(j.childNodes), getText(j.childNodes).upper()),)

            kwargs[item.getAttribute("comment")] = forms.ChoiceField(
                choices=drop_options
            )
        elif item.getAttribute("type") == "mult":
            pass
        elif item.getAttribute("type") == "radio":
            pass
        elif item.getAttribute("type") == "file":
            pass
        elif item.getAttribute("type") == "mult":
            pass
        elif item.getAttribute("type") == "heading":
            pass
        else:
            pass

    custom_form.setFields(kwargs)
    return custom_form

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


def form(request):
    dom = minidom.parse('/home/comrade/Projects/fimm/isbio/breeze/templates/xml/fullExample.xml')
    script_name = dom.getElementsByTagName("rScript")[0].getAttribute("name")
    node = dom.getElementsByTagName("inline")[0]
    script_inline = getText(node.childNodes)

    return render_to_response('forms/base_form.html', {'name': script_name, 'inline': script_inline})




def send_zipfile(request):
    response = HttpResponse(content_type='String')
    response['Content-Disposition'] = 'attachment; filename="/home/comrade/Projects/fimm/isbio/breeze/static/dp.png"'

#    temp = tempfile.TemporaryFile()
#    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
#    for index in range(10):
#        filename = __file__ # Select your files here.
#        archive.write(filename, 'file%d.txt' % index)
#    archive.close()
#    wrapper = FileWrapper(temp)
#    response = HttpResponse(wrapper, content_type='application/zip')
#    response['Content-Disposition'] = 'attachment; filename=test.zip'
#    response['Content-Length'] = temp.tell()
#    temp.seek(0)
#    return response

    return response

def search_form(request):
    return render_to_response('search_form/search_form.html')


def result(request):
    polot_type = request.GET.getlist('plot')
    path = '/home/comrade/Projects/fimm/isbio/breeze/r_scripts/data.r'
    r.assign('path', path)
    r.assign('option', polot_type)
    r('source(path)')
    r('test(toString(option))')
    image_file = open("/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png", 'rb').read()
#    return render_to_response('/jobs.html')
    return HttpResponse(image_file, mimetype='image/png')

