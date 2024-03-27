from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def FilterDesignExamplesView(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, './DesignExamples/Filters/filter_designs.html')


def SteppedLPF_o3_2GHz_View(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, './DesignExamples/Filters/LPF/SteppedLPF_o3_2GHz.html')