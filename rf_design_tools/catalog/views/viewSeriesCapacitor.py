from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import ParallelResistorForm
from catalog.forms import SeriesCapacitorForm


def CseriesDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'SeriesCapacitor/docs/Cseries_doc.html')



################################################################################################
#
#      FORM #4 - SERIES CAPACITOR TOOL
#
#

def parseCstring(C):
    C = C.lower()
    try:
        index_farad = C.find('f')
        
        # Remove F unit
        if index_farad != -1:
            C = C[0 : index_farad : ] + C[index_farad + 1 : :]

        # Remove blank spaces from the string
        if index_farad != -1:
            C = C.replace(" ", "")

        L = len(C)

        # NANOFARAD
        index=C.find('n')
        if index != -1:
            if index == 0:
                a = 0
            else:
                a = float(C[0:index])

            if L > index+1:
                b = C[index+1:L]
                Lb = len(b)
                b = float(b)
                if (a < 0 or b < 0):
                    return -1
                else:
                    return a*1e-9+b*pow(10, (-10-(Lb-1)))
            else:
                if a < 0:
                    return -1
                else:
                    return a*1e-9
        # MICROFARAD
        index=C.find('u')
        if index != -1:
            if index == 0:
                a = 0
            else:
                a = float(C[0:index])

            if L > index+1:
                b = C[index+1:L]
                Lb = len(b)
                b = float(b)
                if (a < 0 or b < 0):
                    return -1
                else:
                    return a*1e-6+b*pow(10, (-7-(Lb-1)))
            else:
                if a < 0:
                    return -1
                else:
                    return a*1e-6

        # PICOFARAD
        index=C.find('p')
        if index != -1:
            if index == 0:
                a = 0
            else:
                a = float(C[0:index])
            if L > index+1:
                b = C[index+1:L]
                Lb = len(b)
                b = float(b)
                if (a < 0 or b < 0):
                    return -1
                else:
                    return a*1e-12+b*pow(10, (-13-(Lb-1)))
            else:
                if a < 0:
                    return -1
                else:
                    return a*1e-12

        C = float(C)
        if C < 0:
            C = -1
    except:
        C = -1
    
    return C

def getValueWithUnits(val, unit):
    prefix = ''
    # Lower than 1
    if val < 1:
        if val < 0.5e-12:
            # femto
            val *= 1e15
            prefix = 'f'
        else:
            if val < 0.5e-9:
                # pico
                val *= 1e12
                prefix = 'p'
            else:
                if val < 0.5e-6:
                    # nano
                    val *= 1e9
                    prefix = 'n'
                else:
                    if val < 0.5e-3:
                        # micro
                        val *= 1e6
                        prefix = 'u'
                    else:
                        if val < 0.5:
                            # mili
                            val *= 1e3
                            prefix = 'm'
    else:
        if val > 1e3:
            # Higher than 1

            if val > 1e9:
                # Giga
                val *= 1e-9
                prefix = 'G'
            else:
                if val > 1e6:
                    # Mega
                    val *= 1e6
                    prefix = 'M'
                else:
                    if val > 1e3:
                        # kilo
                        val *= 1e3
                        prefix = 'k'
        else:
            # Value between 1 and 1k
            prefix = ''

    if prefix == None:
        return str(round(val, 2)) + ' ' + unit
    else:
        return str(round(val, 2)) + ' ' + prefix + unit

def CseriesView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_Cseries = SeriesCapacitorForm(request.POST)
        
        if form_Cseries.is_valid():

            # Get data from the Rparallel form
            C1_ = form_Cseries.cleaned_data['C1'].lower()
            C2_ = form_Cseries.cleaned_data['C2'].lower()

            # Calculate R1
            C1 = parseCstring(C1_)

            # Calculate R2
            C2 = parseCstring(C2_)

            # Calculations
            if (C1 == -1):
                #Error: Problem in C1
                context['Ceq'] = '-1'
            else:
                if (C2 == -1):
                    #Error: Problem in C2
                    context['Ceq'] = '-2'
                else:
                    if (C1 == 0 and C2 == 0):
                        # Then, the equivalent is an open ckt
                        Ceq = 1e6
                    else:
                        # It's OK
                        Ceq = (C1*C2)/(C1+C2)
                    context['Ceq'] = getValueWithUnits(Ceq, 'F')

            context['form_Cseries'] = form_Cseries
            return render(request, 'SeriesCapacitor/tool/Cseries.html', context)
    else:
        form_Cseries = SeriesCapacitorForm()

    context['form_Cseries']= form_Cseries


    return render(request, 'SeriesCapacitor/tool/Cseries.html', context)