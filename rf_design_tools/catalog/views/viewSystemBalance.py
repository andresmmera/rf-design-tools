from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import SystemBalanceForm


from django.template.loader import render_to_string

def SystemBalanceDocs(request):
    return render(request, 'SystemBalance/docs/SystemBalance_doc.html')

def SystemBalanceView(request):
    return render(request, 'SystemBalance/tool/SystemBalance_tool.html')