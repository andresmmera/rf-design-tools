from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def FilterDesignExamplesView(request):
    # Render the HTML template index.html with the data in the context variable
    return render(request, './DesignExamples/Filters/filter_designs.html')


def SteppedLPF_o3_2GHz_View(request):
    # Render the HTML template index.html with the data in the context variable
    return render(request, './DesignExamples/Filters/LPF/SteppedLPF_o5_2GHz.html')

def CoupledLineBPF_o5_5GHz_View(request):
    # Render the HTML template index.html with the data in the context variable
    return render(request, './DesignExamples/Filters/BPF/CoupledLineBPF_o5_5GHz.html')
