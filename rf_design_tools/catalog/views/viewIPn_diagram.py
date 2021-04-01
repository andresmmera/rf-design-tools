from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import IPn_NF_diagramForm
import math
import numpy as np
import json as simplejson

# Bokeh
from django.shortcuts import render
from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet


def IPn_DiagramDocs(request):
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

# ################################################################################################
# #
# #      INTERCEPTION DIAGRAM PLOT
# #
# #
# Equations
def IIP(P_out, G, Delta, n):
    return (P_out - G) + Delta/(n-1) # RF Design Guide. Vizmuller. pg. 36

def PoutIMN(P_in, n, G, IIPN):
    return n*P_in - (n-1)*IIPN + G

def getPlot(Pin_Upper_Limit, Pout_Upper_Limit, No_dBm, SImin, n, G, CPo, IIPn, OIPn, DUT, freq):
    #Plot intercept diagram
    title = "Interception diagram: " + DUT + ' @ ' + str(freq) + ' MHz' ;
    plot = figure(plot_width=800, plot_height=400, title=title)

    # Plot settings
    xmin = Pin_Upper_Limit - 20;
    xmax = IIPn + 10;
    ymin = No_dBm;
    ymax = OIPn + 10;

    # Calculations
    P_in = np.linspace(xmin, xmax, 100);
    fundamental = P_in + G;
    IMn = PoutIMN(P_in, n, G, IIPn);
    DR = Pin_Upper_Limit - No_dBm;
    CPi = CPo - G + 1;

    # Lines
    plot.line(P_in, fundamental, line_width=2, color="navy", legend_label="Fundamental") # Fundamental
    plot.line(P_in, IMn, line_width=2, color="red", legend_label="IMn") # IMn level
    plot.line(P_in, No_dBm, line_width=2, color="orange", legend_label="Noise floor")# Noise floor

    # Level
    level_x = np.linspace(xmin, Pin_Upper_Limit, 100);
    level_y = Pout_Upper_Limit
    plot.line(level_x, level_y, line_width=2, color="black", line_dash='dotted')

    # Points
    plot.circle([IIPn], [OIPn], size=10, color="navy", alpha=0.5) # Intercept point
    plot.circle([CPi], [CPo], size=10, color="navy", alpha=0.5) # Compression point

    # Arrows
    ## Dynamic range arrow
    shift = 4
    plot.add_layout(Arrow(start=NormalHead(size=10),
                        end=NormalHead(size=10),
                        x_start=Pin_Upper_Limit-shift, 
                        y_start=No_dBm, 
                        x_end=Pin_Upper_Limit-shift, 
                        y_end=Pout_Upper_Limit))
    ## S/I min arrow
    plot.add_layout(Arrow(start=NormalHead(size=10),
                        end=NormalHead(size=10),
                        x_start=Pin_Upper_Limit, 
                        y_start=Pout_Upper_Limit - SImin, 
                        x_end=Pin_Upper_Limit, 
                        y_end=Pout_Upper_Limit))

    plot.xaxis.axis_label = 'Input Power (dBm)';
    plot.yaxis.axis_label = 'Output Power (dBm)';
    plot.legend.location = 'top_left';

    # Text annotations
    # Labels with 90 degree rotation
    source = ColumnDataSource(data=dict(y=[Pout_Upper_Limit-DR/2 - 40, Pout_Upper_Limit-DR/2 - 20, Pout_Upper_Limit-SImin/2 - 25, Pout_Upper_Limit-SImin/2-10],
                                        x=[Pin_Upper_Limit-shift-2, Pin_Upper_Limit-shift, Pin_Upper_Limit-2, Pin_Upper_Limit],
                                        names=['Dynamic Range', str("%.1f" % DR) + ' dB',
                                            'Minimum S/I', str(SImin) + ' dB']))
    labels = LabelSet(x='x', y='y', text='names', source=source, angle=90, angle_units='deg', render_mode='canvas')
    plot.add_layout(labels)

    # Labels without rotation
    source = ColumnDataSource(data=dict(y=[CPo+2, OIPn+2],
                                        x=[CPi-1, IIPn-1],
                                        names=['CP', 'IP'+str(n)]))
    labels = LabelSet(x='x', y='y', text='names', source=source, render_mode='canvas')
    plot.add_layout(labels)
    return plot

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
            DUT = form_ipn_diag.cleaned_data['DUT']
            freq = form_ipn_diag.cleaned_data['freq'] # MHz

            context['n'] = n
 
            # Calculations
            
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
            context['No_dBm'] = No_dBm # Noise floor (scalar) for presenting the data in the HTML template
            context['SI'] = SImin

            ## Bokeh plot
            plot = getPlot(Pin_Upper_Limit, Pout_Upper_Limit, No_dBm, SImin, n, G, CPo, IIPn, OIPn, DUT, freq)

            #Store components 
            script, div = components(plot)
            context['script'] = script
            context['div'] = div
   
            context['form_ipn_diag'] = form_ipn_diag
            return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)
    else:
        # Generate default data
        IIPn = 24.0
        OIPn = 40
        CPi = 4
        CPo = 22
        Pin_Upper_Limit = 6.5
        Pout_Upper_Limit = 22.5
        SImin = 35
        No_dBm = -65.18
        DR = 71.7
        n=3
        G = 16
        DUT = 'PHA-1H+'
        freq = 500;

        # Assign default data for the first run
        context['No_dBm'] = No_dBm # Noise floor (scalar) for presenting the data in the HTML template
        context['SI'] = SImin
        context['DR'] = DR
        context['n'] = n
        context['IIPn'] = IIPn
        context['OIPn'] = OIPn

        form_ipn_diag = IPn_NF_diagramForm()

        ## Bokeh plot
        plot = getPlot(Pin_Upper_Limit, Pout_Upper_Limit, No_dBm, SImin, n, G, CPo, IIPn, OIPn, DUT, freq)

        #Store components 
        script, div = components(plot)
        context['script'] = script
        context['div'] = div

    context['form_ipn_diag']= form_ipn_diag


    return render(request, 'InterceptPoints/tool/InterceptPoints.html', context)