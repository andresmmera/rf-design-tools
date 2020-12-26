from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import BandwidthOctavesForm
import math

def BWOctavesDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'BandwidthOctaves/docs/BandwidthOctaves_doc.html')



################################################################################################
#
#      FORM #5 - BANDWIDTH IN OCTAVES
#
#

def BWOctavesView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_bw_oct = BandwidthOctavesForm(request.POST)
        
        if form_bw_oct.is_valid():

            # Get data from the Rparallel form
            f1 = form_bw_oct.cleaned_data['f1']
            f2 = form_bw_oct.cleaned_data['f2']
 
            # Calculations
            maxf = max(f1, f2)
            minf = min(f1, f2)
            BW_OCT = math.log10(maxf/minf)/math.log10(2)
            Q = (minf + maxf) / (maxf - minf)

            context['BW_OCT'] = round(BW_OCT,1)
            context['Q'] = round(Q, 1)
            context['form_bw_oct'] = form_bw_oct
            return render(request, 'BandwidthOctaves/tool/BandwidthOctaves.html', context)
    else:
        form_bw_oct = BandwidthOctavesForm()

    context['form_bw_oct']= form_bw_oct


    return render(request, 'BandwidthOctaves/tool/BandwidthOctaves.html', context)