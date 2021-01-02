from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import IP3_NF_diagramForm
import math
import numpy as np
import json as simplejson

def IP3_DiagramDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'BandwidthOctaves/docs/BandwidthOctaves_doc.html')



################################################################################################
#
#      FORM #6 - IP3 AND NOISEFLOOR DIAGRAM
#
#
def TwoToneTest_to_IIP3(Pout, G, Delta, n):
    """
    Calculate the input intercept point from the two-tone test
    """
    return (Pout - G) + Delta/(n-1) # RF Design Guide. Vizmuller. pg. 36

def ArrayToString(arr):
    string=''
    for x in arr:
        string += str(x) + ";"
    return string[:-1]

def IP3_DiagramView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_ip3_diag = IP3_NF_diagramForm(request.POST)
        
        if form_ip3_diag.is_valid():

            # Get data from the Rparallel form
            G = form_ip3_diag.cleaned_data['G']
            Pout = form_ip3_diag.cleaned_data['Pout']
            Delta = form_ip3_diag.cleaned_data['Delta']
            n = form_ip3_diag.cleaned_data['n']
            CPo = form_ip3_diag.cleaned_data['CPo']
            SImin = form_ip3_diag.cleaned_data['SImin']
            NF = form_ip3_diag.cleaned_data['NF']
            BW = form_ip3_diag.cleaned_data['BW']*1e6 # MHz
            T = form_ip3_diag.cleaned_data['T']

            context['n'] = n
 
            # Calculations
            # Compression point referred to the input
            context['CPi'] = CPo - (G-1) # dBm
            context['CPo'] = CPo #dBm
            
            # Noise floor
            k = 1.3806503e-23 #J/K
            No = k*T*BW*G*pow(10, .1*NF) #W
            No_dBm = np.round(10*math.log10(No) + 30, 2) #dBm

            # Intercept point
            IIPn = TwoToneTest_to_IIP3(Pout, G, Delta, n)
            OIPn = IIPn + G
            context['IIPn'] = IIPn
            context['OIPn'] = OIPn
            

            # Dynamic range
            Pin_Upper_Limit = IIPn - .5*SImin
            Pout_Upper_Limit = Pin_Upper_Limit + G
            Lower_Limit = No_dBm
            context['DR'] = round(Pin_Upper_Limit - Lower_Limit,1)
            context['Pin_Upper_Limit'] = Pin_Upper_Limit
            context['Pout_Upper_Limit'] = Pout_Upper_Limit

            # Plot settings
            xmin = Pin_Upper_Limit - 20
            xmin = int(math.ceil(xmin / 5)) * 10

            xmax = IIPn + 10
            xmax = int(math.ceil(xmax / 5)) * 5

            ymin = No_dBm
            ymin = int(math.floor(ymin / 5)) * 5

            ymax = OIPn + 10
            ymax = int(math.ceil(ymax / 5)) * 5

            context['xmin'] = xmin
            context['xmax'] = xmax
            context['ymin'] = ymin
            context['ymax'] = ymax

            # Define x-axis (Input Power)
            Pin = np.linspace(xmin, xmax, num=20, retstep=True)
            Pin = np.round(Pin[0]) # Round to 1 decimal

            # Fundamental
            Pout = Pin + G*np.ones(len(Pin))

            # IMn
            IMn = n*Pin + (G-(n-1)*IIPn)*np.ones(len(Pin))

            # Noise floor
            Noise_Floor = No_dBm*np.ones(len(Pin))

            context['Pin'] = ArrayToString(Pin)
            context['Pout'] = ArrayToString(Pout)
            context['IMn'] = ArrayToString(IMn)
            context['Noise_Floor'] = ArrayToString(Noise_Floor) # Noise floor (vector) for the plot
            context['No_dBm'] = No_dBm # Noise floor (scalar) for presenting the data in the HTML template
            context['SI'] = SImin
   
            context['form_ip3_diag'] = form_ip3_diag
            return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)
    else:
        form_ip3_diag = IP3_NF_diagramForm()

    context['form_ip3_diag']= form_ip3_diag


    return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)