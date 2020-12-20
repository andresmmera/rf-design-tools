from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def ReflectionCoefficientDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'Reflection_Coefficient/docs/reflection_coeff_docs.html')



################################################################################################
#
#      FORM #1 - REFLECTION COEFFICIENT
#
#
from catalog.forms import ReflectionCoefficientToImpedanceForm, ImpedanceToReflectionCoefficientForm
from django.http import HttpResponse
from django.template import loader
import math

def CalculateReflectionCoefficientView(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_RtoZ = ReflectionCoefficientToImpedanceForm(request.POST)
        form_ZtoR = ImpedanceToReflectionCoefficientForm(request.POST)

        
        if form_RtoZ.is_valid():
            # Process RtoZ form

            # Get data from the RtoZ form
            Z0 = complex(form_RtoZ.cleaned_data['Z0'], 0)
            gamma_mag = form_RtoZ.cleaned_data['gamma_mag']
            gamma_ang = form_RtoZ.cleaned_data['gamma_ang']     
            gamma = complex(gamma_mag*math.cos((math.pi/180)*gamma_ang), gamma_mag*math.sin((math.pi/180)*gamma_ang))

            if (gamma_mag < 1e-3):
                S11 = -1e3
            else:
                S11 = round(20*math.log10(gamma_mag), 2)
            
            # Calculations
            ZL = Z0*(1+gamma)/(1-gamma)
            ZLR = str(round(ZL.real, 2))
            ZLI = str(round(abs(ZL.imag), 2))
            SWR = str(round((1 + gamma_mag)/(1 - gamma_mag), 2))

            if ZL.imag > 0:
                result = ZLR + ' + j ' + ZLI
            if ZL.imag < 0:
                result = ZLR + ' - j ' + ZLI
            if abs(ZL.imag) < 1e-3:
                result = ZLR

            # Assign context for HTML processing
            context['ZL'] = result
            context['S11'] = S11
            context['SWR'] = SWR

            context['form_RtoZ'] = form_RtoZ
            context['form_ZtoR'] = ImpedanceToReflectionCoefficientForm()
            return render(request, 'Reflection_Coefficient/tool/reflection_coeff.html', context)

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

            gamma_mag = round(math.sqrt(gamma.real*gamma.real + gamma.imag*gamma.imag), 2)
            gamma_ang = round((180/math.pi)*math.atan(gamma.imag / gamma.real), 2)

            SWR = str(round((1 + gamma_mag)/(1 - gamma_mag), 2))

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
            context['form_RtoZ'] = ReflectionCoefficientToImpedanceForm()   
            return render(request, 'Reflection_Coefficient/tool/reflection_coeff.html', context)
    else:
        form_RtoZ = ReflectionCoefficientToImpedanceForm()
        form_ZtoR = ImpedanceToReflectionCoefficientForm()

    context['form_RtoZ'] = form_RtoZ
    context['form_ZtoR'] = form_ZtoR

    return render(request, 'Reflection_Coefficient/tool/reflection_coeff.html', context)