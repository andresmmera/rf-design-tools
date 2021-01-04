from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import IPn_NF_diagramForm
import math
import numpy as np
import json as simplejson

def IPn_DiagramDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'InterceptPoints/docs/InterceptPoints_doc.html')



################################################################################################
#
#      FORM #6 - IPn AND NOISE FLOOR DIAGRAM
#
#
def TwoToneTest_to_IIPn(Pout, G, Delta, n):
    """
    Calculate the input intercept point from the two-tone test
    """
    return (Pout - G) + Delta/(n-1) # RF Design Guide. Vizmuller. pg. 36

def ArrayToString(arr):
    string=''
    for x in arr:
        string += str(x) + ";"
    return string[:-1]

def IPn_DiagramView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_ipn_diag = IPn_NF_diagramForm(request.POST)
        
        if form_ipn_diag.is_valid():

            # Get data from the Rparallel form
            G = form_ipn_diag.cleaned_data['G']
            Pout = form_ipn_diag.cleaned_data['Pout']
            Delta = form_ipn_diag.cleaned_data['Delta']
            n = form_ipn_diag.cleaned_data['n']
            CPo = form_ipn_diag.cleaned_data['CPo']
            SImin = form_ipn_diag.cleaned_data['SImin']
            NF = form_ipn_diag.cleaned_data['NF']
            BW = form_ipn_diag.cleaned_data['BW']*1e6 # MHz
            T = form_ipn_diag.cleaned_data['T']

            context['n'] = n
 
            # Calculations
            # Compression point referred to the input
            context['CPi'] = CPo - (G-1) # dBm
            context['CPo'] = CPo #dBm
            
            # Noise floor
            k = 1.3806503e-23 #J/K
            No = k*T*BW*pow(10, .1*(NF+G)) #W
            No_dBm = np.round(10*math.log10(No) + 30, 2) #dBm

            # Intercept point
            IIPn = TwoToneTest_to_IIPn(Pout, G, Delta, n)
            OIPn = IIPn + G
            context['IIPn'] = round(IIPn,1)
            context['OIPn'] = round(OIPn,1)
            

            # Dynamic range
            Pin_Upper_Limit = (SImin - (n-1)*IIPn)/(1-n)
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
   
            context['form_ipn_diag'] = form_ipn_diag
            return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)
    else:
        # Generate default data
        Pin = [-20.0,-17.0,-14.0,-11.0,-8.0,-6.0,-3.0,0.0,3.0,6.0,9.0,12.0,15.0,18.0,21.0,23.0,26.0,29.0,32.0,35.0]
        Pout = [-4.0,-1.0,2.0,5.0,8.0,10.0,13.0,16.0,19.0,22.0,25.0,28.0,31.0,34.0,37.0,39.0,42.0,45.0,48.0,51.0]
        IMn = [-92.0,-83.0,-74.0,-65.0,-56.0,-50.0,-41.0,-32.0,-23.0,-14.0,-5.0,4.0,13.0,22.0,31.0,37.0,46.0,55.0,64.0,73.0]
        Noise_Floor = [-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14]
        IIPn = 24.0
        OIPn = 40
        CPi = 4
        CPo = 22
        Pin_Upper_Limit = 6.5
        Pout_Upper_Limit = 22.5
        SI = 35
        No_dBm = -65.18
        DR = 71.7
        n=3

        # Assign default data for the first run
        context['Pin'] = ArrayToString(Pin)
        context['Pout'] = ArrayToString(Pout)
        context['IMn'] = ArrayToString(IMn)
        context['Noise_Floor'] = ArrayToString(Noise_Floor) # Noise floor (vector) for the plot
        context['No_dBm'] = No_dBm # Noise floor (scalar) for presenting the data in the HTML template
        context['CPi'] = CPi
        context['CPo'] = CPo
        context['SI'] = SI
        context['DR'] = DR
        context['n'] = n
        context['IIPn'] = IIPn
        context['OIPn'] = OIPn
        context['Pin_Upper_Limit'] = Pin_Upper_Limit
        context['Pout_Upper_Limit'] = Pout_Upper_Limit

        form_ipn_diag = IPn_NF_diagramForm()

    context['form_ipn_diag']= form_ipn_diag


    return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)