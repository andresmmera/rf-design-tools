# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import FILTER_STRUCTURES, RESPONSE_TYPE, MASK_TYPE, ELLIPTIC_TYPE, DC_TYPE, FilterDesignForm

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

from .FilterDesign.FilterDesigner import *

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

def FilterDesignDocs(request):
    return render(request, 'FilterDesign/docs/FilterDesignTool.html')


@csrf_exempt
def FilterDesignToolView(request):
    context = {} 
    if request.method == "POST":
        form_filter_design = FilterDesignForm(request.POST)
        print(form_filter_design.errors)
        if form_filter_design.is_valid():
            #Catch the input data
            index = request.POST.get('Structure', None)
            Structure = FILTER_STRUCTURES[int(index)-1][1]
            print("Structure:", Structure)
            
            index = request.POST.get('DC_Type', None)
            DC_Type = DC_TYPE[int(index)-1][1]
            print("DC_Type:", DC_Type)

            index = request.POST.get('FirstElement', None)
            FirstElement = index
            print("FirstElement:", FirstElement)
            
            index = request.POST.get('Response', None)
            Response = RESPONSE_TYPE[int(index)-1][1]
            print("Response Type:", Response)
            
            index = request.POST.get('EllipticType', None)
            EllipticType = ELLIPTIC_TYPE[int(index)-1][1]
            print("Elliptic Type:", EllipticType)
            
            Ripple = request.POST.get('Ripple', None)
            print("Ripple: ", Ripple, " dB")
            
            a_s = request.POST.get('a_s', None)
            print("a_s: ", a_s, " dB")
            
            PhaseError = request.POST.get('PhaseError', None)
            print("PhaseError: ", PhaseError, " deg")
            
            index = request.POST.get('Mask', None)
            Mask = MASK_TYPE[int(index)-1][1]
            print("Mask: ", Mask)
            
            N = request.POST.get('Order', None)
            print("Order: ", N)
            
            Cutoff = request.POST.get('Cutoff', None)
            print("Cutoff: ", Cutoff, " MHz")
            
            f1 = request.POST.get('f1', None)
            print("f1: ", f1, " MHz")
            
            f2 = request.POST.get('f2', None)
            print("f2: ", f2, " MHz")
            
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

            Xres = request.POST.getlist('Xres[]')
            print(Xres)

            # Filter Design
            designer = Filter()
            designer.Structure = Structure
            designer.DC_Type = DC_Type
            designer.FirstElement = int(FirstElement)
            designer.Response = Response
            designer.EllipticType = EllipticType
            designer.Ripple = float(Ripple)
            designer.a_s = float(a_s)
            designer.PhaseError = float(PhaseError)
            designer.Mask = Mask
            designer.N = int(N)
            designer.fc = float(Cutoff)
            designer.f1 = float(f1)
            designer.f2 = float(f2)
            designer.ZS = float(ZS)
            designer.ZL = float(ZL)
            designer.f_start = float(f_start)
            designer.f_stop = float(f_stop)
            designer.n_points = int(n_points)
            designer.Xres = Xres
            
            Schematic, connections = designer.synthesize()
            svgcode = Schematic.get_imagedata('svg')
            
            # The schematic drawing is stored in a global variable so that the file is generated when the user clicks the download button
            global schematic_drawing
            schematic_drawing = Schematic

            # The design object is stored as a local variable so that the Qucs schematic is generated just when the user clicks the download button
            global design_global
            design_global = designer


            # Calculate S-parameters
            circuit = rf.Circuit(connections)
            a = network2.Network.from_ntwkv1(circuit.network)
            S = a.s.val[:]
            freq = a.frequency.f*1e-6
            S11 = 20*np.log10(np.abs(S[:,1][:,1]))
            S21 = 20*np.log10(np.abs(S[:,1][:,0]))
            
            # Response
            title = Response + " Bandpass Filter, N = "+ str(N) + ", Ripple = " + str(Ripple) + " dB" 
            ResponsePlot = figure(plot_width=800, plot_height=400, title=title, y_range=[-50, 0])
            ResponsePlot.line(freq, S11, line_width=2, color="navy", legend_label="S11")
            ResponsePlot.line(freq, S21, line_width=2, color="red", legend_label="S21")
            ResponsePlot.xaxis.axis_label = 'Frequency (MHz)';
            ResponsePlot.yaxis.axis_label = 'Response (dB)';
            ResponsePlot.legend.location = 'bottom_right';

            # Group delay
            gd = abs(circuit.network.s21.group_delay[:, 0][:, 0]) *1e9 # in ns
            title = "Group Delay " + Response + " Bandpass Filter, N = "+ str(N) + ", Ripple = " + str(Ripple) + " dB" 
            GroupDelayPlot = figure(plot_width=800, plot_height=400, title=title, y_range=[0, 1.1*max(gd)])
            GroupDelayPlot.line(freq, gd, line_width=2, color="navy", legend_label="Group Delay")
            GroupDelayPlot.xaxis.axis_label = 'Frequency (MHz)';
            GroupDelayPlot.yaxis.axis_label = 'Group Delay (ns)';
            GroupDelayPlot.legend.location = 'bottom_right';

            phase = (180/np.pi)*np.angle(S[:,1][:,0])
            GroupDelayPlot.extra_y_ranges = {"phase": Range1d(start=-180, end=180)}
            GroupDelayPlot.add_layout(LinearAxis(y_range_name="phase", axis_label="Phase (deg)"), 'right')
            GroupDelayPlot.line(x=freq, y=phase, legend_label='Phase', 
            y_range_name="phase", color="green")

            # Get warnings
            warning = designer.warning

            response_data = {}
            
            # Prepare objects for the html 
            scriptResponse, divResponse = components(ResponsePlot)
            response_data['scriptResponse'] = scriptResponse
            response_data['divResponse'] = divResponse

            scriptGroupDelay, divGroupDelay = components(GroupDelayPlot)
            response_data['scriptGroupDelay'] = scriptGroupDelay
            response_data['divGroupDelay'] = divGroupDelay

            response_data['warning'] = warning
            response_data['svg'] = svgcode.decode('utf-8')
            context['form_filter_design'] = form_filter_design
            return JsonResponse(response_data)

    else:
        # Generate default data
        form_filter_design = FilterDesignForm()
        # Filter Design
        Response = "Chebyshev"
        Mask = "Lowpass"
        fc = 500
        designer = Filter()
        designer.Structure = "Conventional LC"
        designer.DC_Type = "C-coupled shunt resonators"
        designer.Response = Response
        designer.FirstElement = 2 # First series
        designer.Ripple = 0.01
        designer.Mask = Mask
        designer.N = 5
        designer.fc = fc
        designer.ZS = 50
        designer.ZL = 50
        designer.f_start = 50
        designer.f_stop = 1000
        designer.n_points = 201
        designer.Xres = []

        # Calculate the lowpass prototype coefficients
        designer.getLowpassCoefficients()
        
        # Filter response
        Schematic, connections = designer.synthesize()

        # Drawing
        svgcode = Schematic.get_imagedata('svg')
        schematic_drawing = Schematic # The schematic drawing is stored in a global variable so that the file is generated when the user clicks the download button
        design_global = designer # The design object is stored as a local variable so that the Qucs schematic is generated just when the user clicks the download button


        # Calculate S-parameters
        circuit = rf.Circuit(connections)
        a = network2.Network.from_ntwkv1(circuit.network)
        S = a.s.val[:]
        freq = a.frequency.f*1e-6
        S11 = 20*np.log10(np.abs(S[:,1][:,1]))
        S21 = 20*np.log10(np.abs(S[:,1][:,0]))
        
        # Response
        title = Response + " Bandpass Filter, N = "+ str(designer.N) + ", Ripple = " + str(designer.Ripple) + " dB" 
        ResponsePlot = figure(plot_width=800, plot_height=400, title=title, y_range=[-50, 0])
        ResponsePlot.line(freq, S11, line_width=2, color="navy", legend_label="S11")
        ResponsePlot.line(freq, S21, line_width=2, color="red", legend_label="S21")
        ResponsePlot.xaxis.axis_label = 'Frequency (MHz)';
        ResponsePlot.yaxis.axis_label = 'Response (dB)';
        ResponsePlot.legend.location = 'bottom_right';

        # Group delay
        gd = abs(circuit.network.s21.group_delay[:, 0][:, 0]) *1e9 # in ns
        title = "Group Delay " + Response + " Bandpass Filter, N = "+ str(designer.N) + ", Ripple = " + str(designer.Ripple) + " dB" 
        GroupDelayPlot = figure(plot_width=800, plot_height=400, title=title, y_range=[0, max(gd)+10])
        GroupDelayPlot.line(freq, gd, line_width=2, color="navy", legend_label="Group Delay")
        GroupDelayPlot.xaxis.axis_label = 'Frequency (MHz)';
        GroupDelayPlot.yaxis.axis_label = 'Group Delay (ns)';
        GroupDelayPlot.legend.location = 'bottom_right';

        phase = (180/np.pi)*np.angle(S[:,1][:,0])
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

    context['form_filter_design']= form_filter_design


    return render(request, 'FilterDesign/tool/FilterDesignTool.html', context)

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
def SchematicSVGDownload(request):
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
    