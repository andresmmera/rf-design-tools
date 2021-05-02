from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def ReflectionCoefficientDocs(request):
    return render(request, 'Reflection_Coefficient/docs/reflection_coeff_docs.html')

def ReflectionToolsCatalogView(request):
    return render(request, 'Reflection_Coefficient/tool/reflection_coeff_catalog.html')


################################################################################################
#
#      FORM #1.1 - REFLECTION COEFFICIENT TO IMPEDANCE
#
#
from django.http import HttpResponse
from django.template import loader

def GammaToZView(request):
    return render(request, 'Reflection_Coefficient/tool/gamma_to_Z.html')


################################################################################################
#
#      FORM #1.2 - IMPEDANCE TO REFLECTION COEFFICIENT
#
#
from catalog.forms import ImpedanceToReflectionCoefficientForm, SWRToReflectionCoefficientForm
from django.http import HttpResponse
from django.template import loader
import math
def ZToGammaView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_ZtoR = ImpedanceToReflectionCoefficientForm(request.POST)

        if form_ZtoR.is_valid():
            # Process ZtoR form

            # Get data from the ZtoR form
            Z0 = complex(form_ZtoR.cleaned_data['Z0'], 0)
            ZR = form_ZtoR.cleaned_data['ZR']
            ZI = form_ZtoR.cleaned_data['ZI']
                  
            # Calculations
            ZL = complex(ZR, ZI)
            gamma = (ZL - Z0) / (ZL + Z0)
            if (gamma.real < 1e-3):
                gamma = complex(1e-3, gamma.imag)

            gamma_mag = round(math.sqrt(gamma.real*gamma.real + gamma.imag*gamma.imag), 3)
            gamma_ang = round((180/math.pi)*math.atan(gamma.imag / gamma.real), 2)

            SWR = str(round((1 + gamma_mag)/(1 - gamma_mag), 3))

            if (gamma_mag < 1e-3):
                S11 = -1e3
            else:
                S11 = round(20*math.log10(gamma_mag), 2)
            
            # Assign context for HTML processing
            context['gamma_mag'] = gamma_mag
            context['gamma_ang'] = gamma_ang
            context['S11'] = S11
            context['SWR'] = SWR

            context['form_ZtoR'] = form_ZtoR
            return render(request, 'Reflection_Coefficient/tool/Z_to_gamma.html', context)

    else:
        form_ZtoR = ImpedanceToReflectionCoefficientForm()

    context['form_ZtoR'] = form_ZtoR

    return render(request, 'Reflection_Coefficient/tool/Z_to_gamma.html', context)


################################################################################################
#
#      FORM #1.3 - SWR TO REFLECTION COEFFICIENT
#
#
from catalog.forms import ImpedanceToReflectionCoefficientForm, SWRToReflectionCoefficientForm
from django.http import HttpResponse
from django.template import loader
import math
def SWRtoRView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_SWRtoR = SWRToReflectionCoefficientForm(request.POST)
        
        if form_SWRtoR.is_valid():
            # Process ZtoR form

            # Get data from the ZtoR form
            SWR = form_SWRtoR.cleaned_data['SWR']
                  
            # Calculations
            gamma_mag = (SWR-1)/(SWR+1)

            if (gamma_mag < 1e-3):
                S11 = -1e3
            else:
                S11 = round(20*math.log10(gamma_mag), 2)
            
            # Assign context for HTML processing
            context['gamma_mag'] = round(gamma_mag,3)
            context['S11'] = S11

            context['form_SWRtoR'] = form_SWRtoR
            context['form_RtoZ'] = ReflectionCoefficientToImpedanceForm()
            context['form_ZtoR'] = ImpedanceToReflectionCoefficientForm()

            return render(request, 'Reflection_Coefficient/tool/SWR_to_gamma.html', context)
    else:
        form_SWRtoR = SWRToReflectionCoefficientForm()

    context['form_SWRtoR'] = form_SWRtoR

    return render(request, 'Reflection_Coefficient/tool/SWR_to_gamma.html', context)
