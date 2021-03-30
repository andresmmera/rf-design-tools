from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool

def CapRes_CatalogView(request):
    return render(request, 'Capacitor_Resistor_Calculators/capacitor_resistor_catalog.html')