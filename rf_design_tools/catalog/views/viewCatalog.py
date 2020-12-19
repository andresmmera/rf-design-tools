from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def tools_catalog(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'tools_catalog.html')