from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import FILTER_STRUCTURES, RESPONSE_TYPE, MASK_TYPE, FilterDesignForm

# Bokeh
from django.shortcuts import render
from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet

from django.views.decorators.csrf import csrf_exempt

from .FilterDesigner import Filter

from django.http import JsonResponse

import numpy as np

import matplotlib
matplotlib.use('Agg') # Set the backend here

def FilterDesignDocs(request):
    return render(request, 'FilterDesign/docs/FilterDesignTool.html')


def getPlot(freq, S21, S11, Response, Mask, fc):
    #Plot intercept diagram
    title = "Filter Response: " + Response + ',  ' + Mask + ', fc = '+ str(fc) + ' MHz' 
    plot = figure(plot_width=800, plot_height=400, title=title)

    S21_min = 10*np.floor(np.min(S21)/10)
    if (S21_min > -30):
        S21_min = -30
    plot.y_range.start = S21_min
    plot.y_range.end = 0
    plot.yaxis.ticker = np.linspace(S21_min, 0, round(-S21_min/5)+1)
    # Lines
    plot.line(freq, S21, line_width=2, color="red", legend_label="S21") # S21
    plot.line(freq, S11, line_width=2, color="navy", legend_label="S11") # S11

    plot.xaxis.axis_label = 'frequency (MHz)'
    plot.yaxis.axis_label = 'Response (dB)'
    plot.legend.location = 'bottom_right'

    return plot

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
            index = request.POST.get('FirstElement', None)
            FirstElement = index
            print("FirstElement:", FirstElement)
            index = request.POST.get('Response', None)
            Response = RESPONSE_TYPE[int(index)-1][1]
            print("Response Type:", Response)
            Ripple = request.POST.get('Ripple', None)
            print("Ripple: ", Ripple, " dB")
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
            f_start = request.POST.get('f_start', None)
            print(f_start)
            f_stop = request.POST.get('f_stop', None)
            print(f_stop)
            n_points = request.POST.get('n_points', None)
            print(n_points)

            # Filter Design
            designer = Filter()
            designer.Structure = Structure
            designer.FirstElement = int(FirstElement)
            designer.Response = Response
            designer.Ripple = float(Ripple)
            designer.Mask = Mask
            designer.N = int(N)
            designer.fc = float(Cutoff)
            designer.f1 = float(f1)
            designer.f2 = float(f2)
            designer.ZS = float(ZS)
            designer.f_start = float(f_start)
            designer.f_stop = float(f_stop)
            designer.n_points = int(n_points)

            # Drawing
            Schematic = designer.getCanonicalFilterSchematic()
            
            # Filter response
            freq, S11, S21 = designer.getCanonicalFilterNetwork()
            
            svgcode = Schematic.get_imagedata('svg')
            Schematic.save('schematic.svg')
            ## Bokeh plot
            plot = getPlot(freq, S21, S11, Response, Mask, Cutoff)

            #Store components 
            response_data = {}
            script, div = components(plot)
            response_data['script'] = script
            response_data['div'] = div
            response_data['svg'] = svgcode.decode('utf-8')
            context['form_filter_design'] = form_filter_design
            return JsonResponse(response_data)
            #return HttpResponseRedirect(request, 'FilterDesign/tool/FilterDesignTool.html', context)
            #return render(request, 'FilterDesign/tool/FilterDesignTool.html', context )

    else:
        # Generate default data
        form_filter_design = FilterDesignForm()
        # Filter Design
        Response = "Chebyshev"
        Mask = "Lowpass"
        fc = 500
        designer = Filter()
        designer.Structure = "LC Ladder"
        designer.Response = Response
        designer.Ripple = 0.01
        designer.Mask = Mask
        designer.N = 3
        designer.fc = fc
        designer.ZS = 75
        designer.f_start = 50
        designer.f_stop = 1000
        designer.n_points = 201

        # Drawing
        Schematic = designer.getCanonicalFilterSchematic()
        svgcode = Schematic.get_imagedata('svg')
        
        # Filter response
        freq, S11, S21 = designer.getCanonicalFilterNetwork()

        ## Bokeh plot
        plot = getPlot(freq, S21, S11, Response, Mask, fc)

        #Store components 
        script, div = components(plot)
        context['script'] = script
        context['div'] = div
        context['svg'] = svgcode

    context['form_filter_design']= form_filter_design


    return render(request, 'FilterDesign/tool/FilterDesignTool.html', context)