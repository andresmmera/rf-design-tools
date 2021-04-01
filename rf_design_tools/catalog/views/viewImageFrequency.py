from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# Forms
from catalog.models import Tool
from catalog.forms import ImageFrequency_diagramForm
from catalog.forms import HalfIFForm

# Python stuff
import math
import numpy as np
import json as simplejson
from .utilities import ArrayToString

# Bokeh
from django.shortcuts import render
from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet

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

# ################################################################################################
# #
# #      IMAGE FREQUENCY PLANNING
# #
# #
def getPlot(f_LO_min, f_LO_max, f_RF):
    f_LO = np.linspace(f_LO_min, f_LO_max, 100)
    f_IM = abs(2*f_LO-f_RF)
    f_IF = abs(f_RF-f_LO)
    delta = 2*abs(f_RF-f_LO)

    title = "Image Frequency Diagram for RF = " + str(f_RF) + " MHz"
    plot = figure(plot_width=800, plot_height=400, title=title)

    plot.line(f_LO, f_IM, line_width=2, color="navy", legend_label="Image",) # Image frequency
    plot.line(f_LO, f_IF, line_width=2, color="red", legend_label="IF",) # Intermediate frequency
    plot.line(f_LO, delta, line_width=2, color="green", legend_label="Δ = |fRF - fIM|",) # Distance between the IF and the image frequency

    plot.xaxis.axis_label = 'LO frequency (MHz)'
    plot.yaxis.axis_label = 'frequency (MHz)'
    plot.legend.location = 'top'


    plot.add_layout(Arrow(end=NormalHead(size=10),
                    x_start=f_RF + 10, y_start=f_RF + 400, x_end=1.75*(f_RF-f_LO_min), y_end=1.75*(f_RF-f_LO_min)))
    plot.add_layout(Arrow(end=NormalHead(size=10),
                    x_start=f_RF - 10, y_start=f_RF + 400, x_end=0.75*(f_RF-f_LO_min), y_end=1.75*(f_RF-f_LO_min)))

    source = ColumnDataSource(data=dict(y=[1.5*(f_RF-f_LO_min)+40, 1.5*(f_RF-f_LO_min)+40],
                                        x=[f_RF - 390, f_RF+10],
                                        names=['Low-side injection', 'High-side injection']))

    labels = LabelSet(x='x', y='y', text='names', source=source, render_mode='canvas')

    plot.add_layout(labels)
    return plot


def ImageFrequencyView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_im = ImageFrequency_diagramForm(request.POST)
        
        if form_im.is_valid():

            # Get data from the form
            f_RF = form_im.cleaned_data['f_RF']
            context['f_RF'] = f_RF
            f_LO1 = form_im.cleaned_data['f_LO1']
            f_LO2 = form_im.cleaned_data['f_LO2']
 
            # Calculations
            context['form_im'] = form_im

            ## Bokeh plot
            plot = getPlot(f_LO1, f_LO2, f_RF)

            #Store components 
            script, div = components(plot)
            context['script'] = script
            context['div'] = div

            return render(request, 'FrequencyPlanning/tool/ImageFrequencyPlanning.html', context)
    else:
        ## Bokeh plot
        plot = getPlot(200, 1500, 1000)
            
        #Store components 
        script, div = components(plot)
        context['script'] = script
        context['div'] = div

        form_im = ImageFrequency_diagramForm()

    context['form_im']= form_im


    return render(request, 'FrequencyPlanning/tool/ImageFrequencyPlanning.html', context)


# ################################################################################################
# #
# #      HALF IF
# #
# #
def getplotHalf_IF(required_CI, sensitivity, R_half_IF, f_half_IF_low, f_RF):
    noise_limit = sensitivity - required_CI;
    Pmax_half_IF_int = sensitivity + R_half_IF;

    #Plot intercept diagram
    title = "Half-IF low-side injection interference";
    plot = figure(plot_width=800, plot_height=400, title=title, y_range=(noise_limit-20, Pmax_half_IF_int+20))

    freq = np.linspace(0.8*f_half_IF_low, 1.2*f_RF, 100);
    plot.line(freq, noise_limit, line_width=2, color="navy", line_dash='dotted', legend_label="Noise + Interference Limit") # Fundamental
    plot.line(freq, sensitivity, line_width=2, color="red", line_dash='dotted', legend_label="Receiver Sensitivity") # Fundamental


    # Half-IF interferer
    plot.add_layout(Arrow( end=NormalHead(size=10),
                        x_start=f_half_IF_low, 
                        y_start=noise_limit-20, 
                        x_end=f_half_IF_low, 
                        y_end=Pmax_half_IF_int))

    # Desired signal
    plot.add_layout(Arrow( end=NormalHead(size=10),
                        x_start=f_RF, 
                        y_start=noise_limit-20, 
                        x_end=f_RF, 
                        y_end=sensitivity))

    # Half-IF Rejection
    plot.add_layout(Arrow( start=NormalHead(size=10),
                        end=NormalHead(size=10),
                        x_start=f_RF+20, 
                        y_start=sensitivity, 
                        x_end=f_RF+20, 
                        y_end=Pmax_half_IF_int))

    # C/I
    plot.add_layout(Arrow( start=NormalHead(size=10),
                        end=NormalHead(size=10),
                        x_start=f_RF+20, 
                        y_start=noise_limit, 
                        x_end=f_RF+20, 
                        y_end=sensitivity))

    # Labels
    source = ColumnDataSource(data=dict(y=[Pmax_half_IF_int+10, Pmax_half_IF_int, noise_limit + .5*(sensitivity-noise_limit), sensitivity + .5*(Pmax_half_IF_int-sensitivity), sensitivity],
                                        x=[f_half_IF_low-15, f_half_IF_low-15, f_RF+25, f_RF+25, f_RF-5],
                                        names=['Half-IF' , str(f_half_IF_low) + ' MHz',
                                            'C/I', 'Half-IF Rejection', 'RF']))
    labels = LabelSet(x='x', y='y', text='names', source=source, render_mode='canvas')
    plot.add_layout(labels)


    plot.xaxis.axis_label = 'frequency (MHz)';
    plot.yaxis.axis_label = 'Power (dBm)';
    plot.legend.location = 'top_left';

    return plot;
def HalfIFView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_halfIF = HalfIFForm(request.POST)
        
        if form_halfIF.is_valid():

            # Get data from the form
            f_RF = form_halfIF.cleaned_data['RF']
            f_IF = form_halfIF.cleaned_data['IF']
            R_half_IF = form_halfIF.cleaned_data['R'] # Half-IF rejection
            sensitivity = form_halfIF.cleaned_data['S']
            required_CI = form_halfIF.cleaned_data['CI']
 
            ##############################################3
            # # Calculations
            #   Half-IF calculation
            f_LO_low = f_RF - f_IF
            f_LO_high = f_RF + f_IF
            
            half_IF_low_injection = 0.5*(f_RF + f_LO_low)
            half_IF_high_injection = 0.5*(f_RF + f_LO_high)

            context['f_LO_low'] = f_LO_low
            context['f_LO_high'] = f_LO_high
            context['half_IF_low_injection'] = half_IF_low_injection
            context['half_IF_high_injection'] = half_IF_high_injection

            #  IIP2 requirement
            noise_limit = sensitivity - required_CI
            Pmax_half_IF_int = sensitivity + R_half_IF
            IIP2 = 2*R_half_IF + sensitivity + required_CI
            
            context['IIP2'] = IIP2
            context['form_halfIF'] = form_halfIF

            ## Bokeh plot
            plot = getplotHalf_IF(required_CI, sensitivity, R_half_IF, half_IF_low_injection, f_RF)

            #Store components 
            script, div = components(plot)
            context['script'] = script
            context['div'] = div

            return render(request, 'FrequencyPlanning/tool/halfIF.html', context)
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
        script, div = components(plot)
        context['script'] = script
        context['div'] = div

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
