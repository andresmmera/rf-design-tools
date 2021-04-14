from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import SystemBalanceForm
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

from django.template.loader import render_to_string

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

def SystemBalanceView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_system_balance = SystemBalanceForm(request.POST)

    #    if form_system_balance.is_valid():
        url = request.POST.get('url')
        context['variable'] = 5
        context['form_system_balance'] = SystemBalanceForm()
       
        html = render_to_string( 'Reflection_Coefficient/tool/Z_to_gamma.html', context, request=request )
        res = {'html': html}
        return HttpResponse( simplejson.dumps(res), 'application/json' )
    else:
        form_system_balance = SystemBalanceForm()
    context['form_system_balance']= form_system_balance


    return render(request, 'SystemBalance/tool/SystemBalance_tool.html', context)