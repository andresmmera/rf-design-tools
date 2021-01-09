from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import ImageFrequency_diagramForm
import math
import numpy as np
import json as simplejson
from .utilities import ArrayToString

def ImageFrequencyDocs(request):
    return render(request, 'BandwidthOctaves/docs/BandwidthOctaves_doc.html')

def ImageFrequencyCatalogView(request):
    return render(request, 'ImageFrequency/tool/ImageFrequency_catalog.html')

# ################################################################################################
# #
# #      IMAGE FREQUENCY PLANNING
# #
# #

def ImageFrequencyView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_im = ImageFrequency_diagramForm(request.POST)
        
        if form_im.is_valid():

            # Get data from the form
            f_RF = form_im.cleaned_data['f_RF']
            context['f_RF'] = f_RF
            f_LO1 = form_im.cleaned_data['f_LO1']
            f_LO2 = form_im.cleaned_data['f_LO2']
 
            # Calculations

            # Define x-axis (LO frequency)
            #f_LO = np.linspace(f_LO1, f_LO2, num=20, retstep=True)
            f_LO = np.array([f_LO1, round(f_RF/2), f_RF, f_LO2])
            f_LO = np.round(f_LO) # Round to integer
            context['f_LO'] = ArrayToString(f_LO)

            # Image frequency
            f_IM = np.abs(2*f_LO - f_RF*np.ones(len(f_LO)))
            context['f_IM'] = ArrayToString(f_IM)

            # IF
            f_IF = np.abs(f_RF*np.ones(len(f_LO))-f_LO)
            context['f_IF'] = ArrayToString(f_IF)

            # Difference between the IF frequency and the image frequency
            delta_IM_IF = np.abs(2*f_IF)
            context['delta_IM_IF'] = ArrayToString(delta_IM_IF)

            context['form_im'] = form_im
            return render(request, 'ImageFrequency/tool/ImageFrequencyPlanning.html', context)
    else:
        # Generate default data
        f_LO = [200.0, 500.0, 1000.0, 1500.0]
        f_IM = [600.0, 0.0, 1000.0, 2000.0]
        f_IF = [800.0, 500.0, 0.0, 500.0]
        delta_IM_IF = [1600.0, 1000.0, 0.0, 1000.0]

        context['f_LO'] = ArrayToString(f_LO)
        context['f_IM'] = ArrayToString(f_IM)
        context['f_IF'] = ArrayToString(f_IF)
        context['delta_IM_IF'] = ArrayToString(delta_IM_IF)
        
        form_im = ImageFrequency_diagramForm()

    context['form_im']= form_im


    return render(request, 'ImageFrequency/tool/ImageFrequencyPlanning.html', context)