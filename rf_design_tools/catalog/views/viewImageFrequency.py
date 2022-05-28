from django.shortcuts import render

# Python stuff
import numpy as np

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

def HalfIFView(request):
    return render(request, 'FrequencyPlanning/tool/halfIF.html')


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
