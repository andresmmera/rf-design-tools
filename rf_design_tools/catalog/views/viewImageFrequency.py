from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import ImageFrequency_diagramForm
import math
import numpy as np
import json as simplejson
from .utilities import ArrayToString

from django.shortcuts import render
from bokeh.plotting import figure, output_file, show 
from bokeh.embed import components

from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import Arrow, NormalHead
from bokeh.models import ColumnDataSource, LabelSet

def ImageFrequencyDocs(request):
    return render(request, 'ImageFrequency/docs/ImageFrequency_doc.html')

def SSBMixerNotes(request):
    return render(request, 'ImageFrequency/docs/SSB_Mixer_doc.html')

def ImageFrequency_CatalogNotes(request):
    return render(request, 'ImageFrequency/docs/ImageFrequency_Catalog_doc.html')

def HartleyImageRejectionMixersDocs(request):
    return render(request, 'ImageFrequency/docs/Hartley_Image_Rejection_Mixer_doc.html')

def WeaverImageRejectionMixersDocs(request):
    return render(request, 'ImageFrequency/docs/Weaver_Image_Rejection_Mixer_doc.html')

def ImageFrequencyCatalogView(request):
    return render(request, 'ImageFrequency/tool/ImageFrequency_catalog.html')

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

            return render(request, 'ImageFrequency/tool/ImageFrequencyPlanning.html', context)
    else:
        ## Bokeh plot
        plot = getPlot(200, 1500, 1000)
            
        #Store components 
        script, div = components(plot)
        context['script'] = script
        context['div'] = div

        form_im = ImageFrequency_diagramForm()

    context['form_im']= form_im


    return render(request, 'ImageFrequency/tool/ImageFrequencyPlanning.html', context)