# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import ATTENUATOR_STRUCTURES, AttenuatorDesignForm

# Bokeh
from django.shortcuts import render
from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.models import LinearAxis, Range1d


from django.views.decorators.csrf import csrf_exempt

from .AttenuatorDesign.AttenuatorDesigner import *

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

def AttenuatorDesignDocs(request):
    return render(request, 'AttenuatorDesign/docs/AttenuatorDesign_doc.html')

def AttenuatorDesignDocs_PiTee(request):
    return render(request, 'AttenuatorDesign/docs/AttenuatorDesign_PiTee_doc.html')


@csrf_exempt
def AttenuatorDesignToolView(request):
    context = {} 
    if request.method == "POST":
        form_attenuator_design = AttenuatorDesignForm(request.POST)
        print(form_attenuator_design.errors)
        if form_attenuator_design.is_valid():
            #Catch the input data
            index = request.POST.get('Structure', None)
            Structure = ATTENUATOR_STRUCTURES[int(index)-1][1]
            print("Structure:", Structure)
                        
            Pin = request.POST.get('Pin', None)
            print("Pin: ", Pin, " dBm")
            
            att = request.POST.get('att', None)
            print("att: ", att, " dB")
                        
            f0 = request.POST.get('f0', None)
            print("f0: ", f0, " MHz")
                        
            ZS = request.POST.get('ZS', None)
            print("ZS = ", ZS)
            
            ZL = request.POST.get('ZL', None)
            print("ZL = ", ZL)
            
            f_start = request.POST.get('f_start', None)
            print(f_start)
            
            f_stop = request.POST.get('f_stop', None)
            print(f_stop)
            
            n_points = request.POST.get('n_points', None)
            print(n_points)

            # Attenuator Design
            designer = Attenuator()
            designer.Structure = Structure
            designer.Pin = float(Pin)
            designer.att = float(att)
            designer.f0 = float(f0)
            designer.ZS = float(ZS)
            designer.ZL = float(ZL)
            designer.f_start = float(f_start)
            designer.f_stop = float(f_stop)
            designer.n_points = int(n_points)
            
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

            S11 = 20*np.log10(np.abs(S11))
            S21 = 20*np.log10(np.abs(S21))
            
            # Response
            title = Structure + " Attenuator ("+ str(att) + " dB)"
            ResponsePlot = figure(plot_width=800, plot_height=400, title=title, y_range=[-50, 0])
            ResponsePlot.line(freq, S11, line_width=2, color="navy", legend_label="S11")
            ResponsePlot.line(freq, S21, line_width=2, color="red", legend_label="S21")
            ResponsePlot.xaxis.axis_label = 'Frequency (MHz)';
            ResponsePlot.yaxis.axis_label = 'Response (dB)';
            ResponsePlot.legend.location = 'bottom_right';

            # Group delay
            title = Structure + " Attenuator ("+ str(att) + " dB)"
            GroupDelayPlot = figure(plot_width=800, plot_height=400, title=title, y_range=[0, 1.1*max(gd)])
            GroupDelayPlot.line(freq, gd, line_width=2, color="navy", legend_label="Group Delay")
            GroupDelayPlot.xaxis.axis_label = 'Frequency (MHz)';
            GroupDelayPlot.yaxis.axis_label = 'Group Delay (ns)';
            GroupDelayPlot.legend.location = 'bottom_right';

            GroupDelayPlot.extra_y_ranges = {"phase": Range1d(start=-180, end=180)}
            GroupDelayPlot.add_layout(LinearAxis(y_range_name="phase", axis_label="Phase (deg)"), 'right')
            GroupDelayPlot.line(x=freq, y=phase, legend_label='Phase', 
            y_range_name="phase", color="green")

            # Get warnings
            #warning = designer.warning

            response_data = {}
            
            # Prepare objects for the html 
            scriptResponse, divResponse = components(ResponsePlot)
            response_data['scriptResponse'] = scriptResponse
            response_data['divResponse'] = divResponse

            scriptGroupDelay, divGroupDelay = components(GroupDelayPlot)
            response_data['scriptGroupDelay'] = scriptGroupDelay
            response_data['divGroupDelay'] = divGroupDelay

            #response_data['warning'] = warning
            response_data['svg'] = svgcode.decode('utf-8')
            context['form_attenuator_design'] = form_attenuator_design
            return JsonResponse(response_data)

    else:
        # Generate default data
        form_attenuator_design = AttenuatorDesignForm()
        # Attenuator Design
        designer = Attenuator()
        designer.Structure = "Pi"
        designer.Pin = -10
        designer.att = 10
        designer.f0 = 1000
        designer.ZS = 50
        designer.ZL = 50
        designer.f_start = 50
        designer.f_stop = 1000
        designer.n_points = 201
        
        # Circuit
        Schematic, Network_Type, comp_val = designer.synthesize()

        # Drawing
        svgcode = Schematic.get_imagedata('svg')
        schematic_drawing = Schematic # The schematic drawing is stored in a global variable so that the file is generated when the user clicks the download button
        design_global = designer # The design object is stored as a local variable so that the Qucs schematic is generated just when the user clicks the download button


        # Calculate S-parameters
        [S11, S21] = NetworkResponse(Network_Type, comp_val)
        freq = Network_Type['freq']
        phase = (180/np.pi)*np.angle(S21)
        gd = -(1e9)*np.diff(np.angle(S21))/(2*np.pi*freq[:-1]); # Group delay [ns]

        S11 = 20*np.log10(np.abs(S11))
        S21 = 20*np.log10(np.abs(S21))
        
        # Response
        title = designer.Structure + " Attenuator ("+ str(designer.att) + " dB) " 
        ResponsePlot = figure(plot_width=800, plot_height=400, title=title, y_range=[-50, 0])
        ResponsePlot.line(freq, S11, line_width=2, color="navy", legend_label="S11")
        ResponsePlot.line(freq, S21, line_width=2, color="red", legend_label="S21")
        ResponsePlot.xaxis.axis_label = 'Frequency (MHz)';
        ResponsePlot.yaxis.axis_label = 'Response (dB)';
        ResponsePlot.legend.location = 'bottom_right';

        # Group delay
        title = designer.Structure + " Attenuator ("+ str(designer.att) + " dB) " 
        GroupDelayPlot = figure(plot_width=800, plot_height=400, title=title, y_range=[0, max(gd)+10])
        GroupDelayPlot.line(freq, gd, line_width=2, color="navy", legend_label="Group Delay")
        GroupDelayPlot.xaxis.axis_label = 'Frequency (MHz)';
        GroupDelayPlot.yaxis.axis_label = 'Group Delay (ns)';
        GroupDelayPlot.legend.location = 'bottom_right';

        GroupDelayPlot.extra_y_ranges = {"phase": Range1d(start=-180, end=180)}
        GroupDelayPlot.add_layout(LinearAxis(y_range_name="phase", axis_label="Phase (deg)"), 'right')
        GroupDelayPlot.line(x=freq, y=phase, legend_label='Phase', 
        y_range_name="phase", color="green")

        # Prepare objets for the html 
        scriptResponse, divResponse = components(ResponsePlot)
        context['scriptResponse'] = scriptResponse
        context['divResponse'] = divResponse

        scriptGroupDelay, divGroupDelay = components(GroupDelayPlot)
        context['scriptGroupDelay'] = scriptGroupDelay
        context['divGroupDelay'] = divGroupDelay

        context['svg'] = svgcode # Schematic

    context['form_attenuator_design']= form_attenuator_design


    return render(request, 'AttenuatorDesign/tool/AttenuatorDesignTool.html', context)

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

    if(Network_Type['Network'] == 'Pi'):
        Rshunt1 = comp_val['Rshunt1']
        Rseries = comp_val['Rseries']
        Rshunt2 = comp_val['Rshunt2']

        S11 = (Rseries*Rshunt1*Rshunt2 + (Rseries*Rshunt1 + Rshunt1*Rshunt2)*ZL - ((Rseries + Rshunt1)*Rshunt2 + (Rseries + Rshunt1 + Rshunt2)*ZL)*ZS)/(Rseries*Rshunt1*Rshunt2 + (Rseries*Rshunt1 + Rshunt1*Rshunt2)*ZL + ((Rseries + Rshunt1)*Rshunt2 + (Rseries + Rshunt1 + Rshunt2)*ZL)*ZS)
        S21 = 2*Rshunt1*Rshunt2*ZL*ZS/((Rseries*Rshunt1*Rshunt2 + (Rseries*Rshunt1 + Rshunt1*Rshunt2)*ZL + ((Rseries + Rshunt1)*Rshunt2 + (Rseries + Rshunt1 + Rshunt2)*ZL)*ZS)*np.sqrt(ZL*ZS))

    elif(Network_Type['Network'] == 'Tee'):
        Rseries1 = comp_val['Rseries1']
        Rshunt = comp_val['Rshunt']
        Rseries2 = comp_val['Rseries2']

        S11 = (Rseries1*Rseries2 + (Rseries1 + Rseries2)*Rshunt + (Rseries1 + Rshunt)*ZL - (Rseries2 + Rshunt + ZL)*ZS)/(Rseries1*Rseries2 + (Rseries1 + Rseries2)*Rshunt + (Rseries1 + Rshunt)*ZL + (Rseries2 + Rshunt + ZL)*ZS)
        S21 = 2*Rshunt*ZL*ZS/((Rseries1*Rseries2 + (Rseries1 + Rseries2)*Rshunt + (Rseries1 + Rshunt)*ZL + (Rseries2 + Rshunt + ZL)*ZS)*np.sqrt(ZL*ZS))
    elif(Network_Type['Network'] == 'Bridged-Tee'):
        Rseries = comp_val['Rseries']
        Rshunt = comp_val['Rshunt']
        Z0 = comp_val['Z0']

        S11 = (2*Rseries*Rshunt*Z0 + Rseries*Z0**2 + (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2)*ZL - (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2 + (Rseries + 2*Z0)*ZL)*ZS)/(2*Rseries*Rshunt*Z0 + Rseries*Z0**2 + (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2)*ZL + (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2 + (Rseries + 2*Z0)*ZL)*ZS)
        S21 = 2*(Rseries*Rshunt + 2*Rshunt*Z0 + Z0**2)*ZL*ZS/((2*Rseries*Rshunt*Z0 + Rseries*Z0**2 + (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2)*ZL + (Rseries*Rshunt + (Rseries + 2*Rshunt)*Z0 + Z0**2 + (Rseries + 2*Z0)*ZL)*ZS)*np.sqrt(ZL*ZS))

    return np.ones(len(freq))*S11, np.ones(len(freq))*S21