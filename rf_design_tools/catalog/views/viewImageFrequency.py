from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # Allow ajax

# Forms
from catalog.models import Tool
from catalog.forms import HalfIFForm

# Python stuff
import math
import numpy as np
import json as simplejson
from .utilities import ArrayToString

# Bokeh
from django.shortcuts import render

def ImageFrequencyDocs(request):
    return render(request, 'FrequencyPlanning/docs/ImageFrequency_doc.html')

def SSBMixerNotes(request):
    return render(request, 'FrequencyPlanning/docs/SSB_Mixer_doc.html')

def ImageFrequency_CatalogNotes(request):
    return render(request, 'FrequencyPlanning/docs/ImageFrequency_Catalog_doc.html')

def HartleyImageRejectionMixersDocs(request):
    return render(request, 'FrequencyPlanning/docs/Hartley_Image_Rejection_Mixer_doc.html')

def WeaverImageRejectionMixersDocs(request):
    return render(request, 'FrequencyPlanning/docs/Weaver_Image_Rejection_Mixer_doc.html')

def ImageFrequencyCatalogView(request):
    return render(request, 'FrequencyPlanning/tool/ImageFrequency_catalog.html')


def ImageFrequencyView(request):
    return render(request, 'FrequencyPlanning/tool/ImageFrequencyPlanning.html')


# ################################################################################################
# #
# #      HALF IF
# #
# #
def getplotHalf_IF(required_CI, sensitivity, R_half_IF, f_half_IF_low, f_RF):
    noise_limit = sensitivity - required_CI;
    Pmax_half_IF_int = sensitivity + R_half_IF;


    freq = np.linspace(0.8*f_half_IF_low, 1.2*f_RF, 100);

    return freq, noise_limit, sensitivity;

@csrf_exempt
def HalfIFView(request):
    context = {} 
    if request.method == "POST":
        # Get data from the form
        f_RF = request.POST.get('RF', None)
        f_IF = request.POST.get('IF', None)
        R_half_IF = request.POST.get('HIF_Rejection', None)
        sensitivity = request.POST.get('Sensitivity', None)
        required_CI = request.POST.get('CI', None)
        f_RF = float(f_RF)
        f_IF = float(f_IF)
        R_half_IF = float(R_half_IF)
        sensitivity = float(sensitivity)
        required_CI = float(required_CI)
        ##############################################3
        # # Calculations
        #   Half-IF calculation
        f_LO_low = f_RF - f_IF
        f_LO_high = f_RF + f_IF
        
        half_IF_low_injection = 0.5*(f_RF + f_LO_low)
        half_IF_high_injection = 0.5*(f_RF + f_LO_high)

            #  IIP2 requirement
        noise_limit = sensitivity - required_CI
        Pmax_half_IF_int = sensitivity + R_half_IF
        IIP2 = 2*R_half_IF + sensitivity + required_CI
        
        #Store components 

        response_data = {}
        freq = np.round_(np.linspace(0.8*half_IF_low_injection, 1.2*f_RF, 100))
        response_data['freq'] =freq.tolist()
        response_data['noise_limit'] = noise_limit
        response_data['Pmax_half_IF_int'] = Pmax_half_IF_int
        response_data['IIP2'] = IIP2

        response_data['f_LO_low'] = f_LO_low
        response_data['f_LO_high'] = f_LO_high
        response_data['half_IF_low_injection'] = half_IF_low_injection
        response_data['half_IF_high_injection'] = half_IF_high_injection

        response_data['title'] = 'Half-IF Spurious Diagram (RF = ' + str(f_RF) + ' MHz,  IF = ' + str(f_IF) + ' MHz)' 
        
        return JsonResponse(response_data)
    else:
        # Default values
        required_CI = 35 #dB
        sensitivity = -110 #dBm
        R_half_IF = 60 #dB
        half_IF_low_injection = 850 # MHz
        f_RF = 900 # MHz
        ## Bokeh plot
        plot = getplotHalf_IF(required_CI, sensitivity, R_half_IF, half_IF_low_injection, f_RF)
            
        #Store components 
        context['script'] = 'script'
        context['div'] = 'div'

        form_halfIF = HalfIFForm()

    context['form_halfIF']= form_halfIF


    return render(request, 'FrequencyPlanning/tool/halfIF.html', context)


# ################################################################################################
# #
# #      SECONDARY IMAGE
# #
# #
from catalog.forms import SecondaryImageForm
from django.http import HttpResponse
from django.template import loader
import math

def SecondaryImageView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_2nd_Image = SecondaryImageForm(request.POST)
        
        if form_2nd_Image.is_valid():
            # Get data from the form
            f_IF1 = form_2nd_Image.cleaned_data['f_IF1']
            f_IF2 = form_2nd_Image.cleaned_data['f_IF2']
            f_RF = form_2nd_Image.cleaned_data['f_RF']

            # Calculations
            f_LO1 = f_RF - f_IF1; # 1st LO frequency
            f_LO2 = f_IF1 - f_IF2; #2nd LO frequency

            fIM2_1 = 2*f_LO2 + 2*f_LO1 - f_RF
            fIM2_2 = -2*f_LO2+f_RF

            # Assign context for HTML processing
            context['f_IM1'] = fIM2_1
            context['f_IM2'] = fIM2_2

            context['f_LO1'] = f_LO1
            context['f_LO2'] = f_LO2

            context['f_IF1'] = f_IF1
            context['f_IF2'] = f_IF2

            context['f_RF'] = f_RF

            context['form_2nd_Image'] = form_2nd_Image
            return render(request, 'FrequencyPlanning/tool/SecondaryImage_tool.html', context)
    else:
        form_2nd_Image = SecondaryImageForm()

    context['form_2nd_Image'] = form_2nd_Image


    return render(request, 'FrequencyPlanning/tool/SecondaryImage_tool.html', context)
