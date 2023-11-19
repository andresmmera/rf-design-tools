from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool

from django.template.loader import render_to_string

def RFPowerConversionDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'RF_Power_Converter/docs/RF_power_converter_doc.html')

def CalculatePowerConverterView(request):
    return render(request, 'RF_Power_Converter/tool/RF_power_converter.html')