from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import ParallelResistorForm


def RparallelDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'ParallelResistor/docs/Rparallel_doc.html')



################################################################################################
#
#      FORM #3 - PARALLEL RESISTOR TOOL
#
#

def parseRstring(R):
    L = len(R)
    index=R.find('k')

    if index != -1:
        a = float(R[0:index])
        if L > index+1:
            b = float(R[index+1:L])
            return a*1e3+b*1e2
        else:
            return a*1e3
    return float(R)

def RparallelView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_Rparallel = ParallelResistorForm(request.POST)
        
        if form_Rparallel.is_valid():

            # Get data from the Rparallel form
            R1_ = form_Rparallel.cleaned_data['R1'].lower()
            R2_ = form_Rparallel.cleaned_data['R2'].lower()

            # Calculate R1
            R1 = parseRstring(R1_)

            # Calculate R2
            R2 = parseRstring(R2_)

            # Calculations
            Req = (R1*R2)/(R1+R2)

            # Assign context for HTML processing
            context['Req'] = round(Req,1)

            context['form_Rparallel'] = form_Rparallel
            return render(request, 'ParallelResistor/tool/Rparallel.html', context)
    else:
        form_Rparallel = ParallelResistorForm()

    context['form_Rparallel']= form_Rparallel


    return render(request, 'ParallelResistor/tool/Rparallel.html', context)