from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool

def FreeSpacePathLossView(request):
    return render(request, 'FreeSpacePathLoss/tool/FreeSpacePathLoss.html')

def FreeSpacePathLossDocs(request):
    return render(request, 'FreeSpacePathLoss/docs/FreeSpacePathLoss_doc.html')