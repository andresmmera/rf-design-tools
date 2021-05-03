from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool

def WavelengthFrequencyDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'WavelengthCalculator/docs/WavelengthCalculator_doc.html')

def WavelengthFrequencyView(request):
    return render(request, 'WavelengthCalculator/tool/WavelengthCalculator.html')