# Copyright 2020-2022 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import MATCHING_NETWORK_STRUCTURES
from catalog.forms import MASK_TYPE


from django.views.decorators.csrf import csrf_exempt # Allow ajax

from .LumpedTransmissionLineDesign.LumpedTransmissionLineDesigner import *

from django.http import JsonResponse

import numpy as np

import matplotlib
matplotlib.use('Agg') # Set the backend here

# Import modules for file download
import mimetypes
import os
from django.http.response import HttpResponse

schematic_drawing = None # Global variable storing the schematic. By doing this, the schematic file is generated just when the user clicks download
design_global = None

def LumpedTransmissionLineToolDocs(request):
    return render(request, 'LumpedTransmissionLines/docs/LumpedTransmissionLines_doc.html')


@csrf_exempt
def LumpedTransmissionLineToolView(request):
    context = {} 
    if request.method == "POST":
        #Catch the input data
        index = request.POST.get('Structure', None)
        if (index=='1'):
            Structure = 'Tee-Type'
        else:
            Structure = 'Pi-Type'

        #print("Structure:", Structure)

        index = request.POST.get('Mask', None)
        Mask = MASK_TYPE[int(index)-1][1]                    
        f0 = request.POST.get('f0', None)
        Z0 = request.POST.get('Z0', None)
        ZS = request.POST.get('ZS', None)
        ZL = request.POST.get('ZL', None)

        length = request.POST.get('length', None)       
        f_start = request.POST.get('f_start', None)
        f_stop = request.POST.get('f_stop', None)
        f0_span = request.POST.get('f0_span', None)        
        f_span = request.POST.get('f_span', None)
        sweep_mode = request.POST.get('sweep_mode', None)
        n_points = request.POST.get('n_points', None)

        # Lumped Transmission Line Design
        designer = LumpedTransmissionLine()
        designer.Structure = Structure
        designer.f0 = float(f0)
        designer.Z0 = float(Z0)
        designer.ZS = float(ZS)
        designer.ZL = float(ZL)
        designer.length = float(length)
        designer.f_start = float(f_start)
        designer.f_stop = float(f_stop)
        designer.n_points = int(n_points)
        designer.f0_span = float(f0_span)
        designer.f_span = float(f_span)
        designer.sweep_mode = int(sweep_mode)
        designer.Mask = Mask
        
        Schematic, Network_Type, comp_val = designer.synthesize()
        svgcode = Schematic.get_imagedata('svg')
        
        # The schematic drawing is stored in a global variable so that the file is generated when the user clicks the download button
        global schematic_drawing
        schematic_drawing = Schematic

        # The design object is stored as a local variable so that the Qucs schematic is generated just when the user clicks the download button
        global design_global
        design_global = designer


        # Calculate S-parameters
        [S11, S21] = NetworkResponse(Network_Type, comp_val)
        freq = Network_Type['freq']
        phase = (180/np.pi)*np.angle(S21)
        gd = -(1e9)*np.diff(np.angle(S21))/(2*np.pi*freq[:-1]); # Group delay [ns]
        
        
        S11 = np.where(S11 == 0, 1e-12, S11) # Prevent display errors in the JS side for having S11 = 0
        S11 = 20*np.log10(np.abs(S11))
        S21 = 20*np.log10(np.abs(S21))
        
        # Response
        title = Structure + " Lumped Equivalent (Z" + "\u2080 = " + Z0 + "\u03A9, l = " + length + "\u03BB" + ")"

        response_data = {}

        # Prepare objects for the html 
        response_data['freq'] =(freq*1e-6).tolist()
        response_data['S11'] = S11.tolist()
        response_data['S21'] = S21.tolist()
        response_data['title'] = title
        #response_data['warning'] = warning
        response_data['svg'] = svgcode.decode('utf-8')
        return JsonResponse(response_data)


    return render(request, 'LumpedTransmissionLines/tool/LumpedTransmissionLineTool.html', context)

# Source: https://linuxhint.com/download-the-file-in-django/
@csrf_exempt
def QucsFilterDownload(request):
    # Create the Qucs schematic from the designer specs
    global design_global
    QucsSchematic = design_global.getQucsSchematic()

    # Save schematic to file
    filename = "QucsSchematic-export.sch"
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = BASE_DIR + '/templates/download/' + filename
    schematic_name = filepath
    schematic_file = open(schematic_name, "w")
    n = schematic_file.write(QucsSchematic)
    schematic_file.close()

    # Open the file for reading content
    path = open(filepath, 'r')
    # Set the mime type
    mime_type, _ = mimetypes.guess_type(filepath)
    # Set the return value of the HttpResponse
    response = HttpResponse(path, content_type=mime_type)
    # Set the HTTP header for sending to browser
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    # Return the response value
    return response

# Source: https://linuxhint.com/download-the-file-in-django/
@csrf_exempt
def SchematicSVGDownload_Attenuator(request):
    global schematic_drawing # Take the schematic from the global button
    # Generate the SVG file
    filename = 'schematic.svg'
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = BASE_DIR + '/templates/download/' + filename
    schematic_drawing.save(filepath)

    # Prepare to download
    ########################################################
    # Define Django project base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Define text file name
    print("Location of the schematic:", BASE_DIR)
    filename = 'schematic.svg'
    # Define the full file path
    filepath = BASE_DIR + '/templates/download/' + filename
    # Open the file for reading content
    path = open(filepath, 'r')
    # Set the mime type
    mime_type, _ = mimetypes.guess_type(filepath)
    # Set the return value of the HttpResponse
    response = HttpResponse(path, content_type=mime_type)
    # Set the HTTP header for sending to browser
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    # Return the response value
    return response
    

def NetworkResponse(Network_Type, comp_val):
    I = 1j
    pi = np.pi

    ZS = comp_val['ZS']
    ZL = comp_val['ZL']
    freq = Network_Type['freq'];

    if((comp_val['topology'][0] == 'CP') and (comp_val['topology'][1] == 'LS')):
        C = comp_val['values_network'][0]
        L = comp_val['values_network'][1]
        
        S11 = (-8*I*pi**3*C**2*L*ZL*ZS*freq**3 + 4*(pi**2*C*L*ZL - pi**2*C*L*ZS)*freq**2 - 2*(-2*I*pi*C*ZL*ZS + I*pi*L)*freq - ZL + ZS)/(8*I*pi**3*C**2*L*ZL*ZS*freq**3 + 4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + 2*(-2*I*pi*C*ZL*ZS - I*pi*L)*freq - ZL - ZS)
        S21 = -2*ZL*ZS/((8*I*pi**3*C**2*L*ZL*ZS*freq**3 + 4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + 2*(-2*I*pi*C*ZL*ZS - I*pi*L)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

    elif((comp_val['topology'][0] == 'LP') and (comp_val['topology'][1] == 'CS')):
        L = comp_val['values_network'][0]
        C = comp_val['values_network'][1]
        S11 = (8*(pi**3*C*L**2*ZL - pi**3*C*L**2*ZS)*freq**3 - 4*(-2*I*pi**2*C*L*ZL*ZS + I*pi**2*L**2)*freq**2 - I*ZL*ZS - 2*(pi*L*ZL - pi*L*ZS)*freq)/(8*(pi**3*C*L**2*ZL + pi**3*C*L**2*ZS)*freq**3 + 4*(-2*I*pi**2*C*L*ZL*ZS - I*pi**2*L**2)*freq**2 + I*ZL*ZS - 2*(pi*L*ZL + pi*L*ZS)*freq)
        S21 = 16*pi**3*C*L**2*ZL*ZS*freq**3/((8*(pi**3*C*L**2*ZL + pi**3*C*L**2*ZS)*freq**3 + 4*(-2*I*pi**2*C*L*ZL*ZS - I*pi**2*L**2)*freq**2 + I*ZL*ZS - 2*(pi*L*ZL + pi*L*ZS)*freq)*np.sqrt(ZL*ZS))

    elif((comp_val['topology'][0] == 'CS') and (comp_val['topology'][1] == 'LP')):
        C = comp_val['values_network'][0]
        L = comp_val['values_network'][1]

        S11 = (8*(pi**3*C**2*L*ZL - pi**3*C**2*L*ZS)*freq**3 - 4*(-I*pi**2*C**2*ZL*ZS + 2*I*pi**2*C*L)*freq**2 - 2*(pi*C*ZL - pi*C*ZS)*freq + I)/(8*(pi**3*C**2*L*ZL + pi**3*C**2*L*ZS)*freq**3 + 4*(-I*pi**2*C**2*ZL*ZS - 2*I*pi**2*C*L)*freq**2 - 2*(pi*C*ZL + pi*C*ZS)*freq + I)
        S21 = 16*pi**3*C**2*L*ZL*ZS*freq**3/((8*(pi**3*C**2*L*ZL + pi**3*C**2*L*ZS)*freq**3 + 4*(-I*pi**2*C**2*ZL*ZS - 2*I*pi**2*C*L)*freq**2 - 2*(pi*C*ZL + pi*C*ZS)*freq + I)*np.sqrt(ZL*ZS))

    elif((comp_val['topology'][0] == 'LS') and (comp_val['topology'][1] == 'CP')):
        L = comp_val['values_network'][0]
        C = comp_val['values_network'][1]

        S11 = (8*I*pi**3*C*L**2*freq**3 + 4*(pi**2*C*L*ZL - pi**2*C*L*ZS)*freq**2 + 2*(I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL + ZS)/(8*I*pi**3*C*L**2*freq**3 + 4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + 2*(-I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)
        S21 = -2*ZL*ZS/((8*I*pi**3*C*L**2*freq**3 + 4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + 2*(-I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)*np.sqrt(ZL*ZS))


    return np.ones(len(freq))*S11, np.ones(len(freq))*S21