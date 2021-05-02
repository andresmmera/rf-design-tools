from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool

def BWOctavesDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'BandwidthOctaves/docs/BandwidthOctaves_doc.html')

def BWOctavesView(request):
    return render(request, 'BandwidthOctaves/tool/BandwidthOctaves.html')