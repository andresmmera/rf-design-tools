from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool

def index(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html')

def reflection_coeff(request):
    return render(request, 'reflection_coeff.html')

from django.views import generic

class ToolListView(generic.ListView):
    model = Tool


from .forms import ReflectionCoefficientToImpedanceForm, ImpedanceToReflectionCoefficientForm
from django.http import HttpResponse
from django.template import loader
import math

def CalculateReflectionCoefficientForm(request):
    context = {} 
    if request.method == "POST":
        #Catch the forms
        form_RtoZ = ReflectionCoefficientToImpedanceForm(request.POST)
        form_ZtoR = ImpedanceToReflectionCoefficientForm(request.POST)

        
        if form_RtoZ.is_valid():
            # Process RtoZ form
            Z0 = complex(form_RtoZ.cleaned_data['Z0'], 0)
            gamma_mag = form_RtoZ.cleaned_data['gamma_mag']
            gamma_ang = form_RtoZ.cleaned_data['gamma_ang']     
            gamma = complex(gamma_mag*math.cos((math.pi/180)*gamma_ang), gamma_mag*math.sin((math.pi/180)*gamma_ang))

            context['form_RtoZ'] = form_RtoZ
            
            ZL = Z0*(1+gamma)/(1-gamma)
            ZLR = str(round(ZL.real, 2))
            ZLI = str(round(abs(ZL.imag), 2))

            if ZL.imag > 0:
                result = ZLR + ' + j ' + ZLI
            if ZL.imag < 0:
                result = ZLR + ' - j ' + ZLI
            if abs(ZL.imag) < 1e-3:
                result = ZLR

            context['ZL'] = result
            context['form_ZtoR'] = ImpedanceToReflectionCoefficientForm()
            return render(request, 'reflection_coeff.html', context)

        if form_ZtoR.is_valid():
            # Process ZtoR form
            Z0 = complex(form_ZtoR.cleaned_data['Z0'], 0)
            ZR = form_ZtoR.cleaned_data['ZR']
            ZI = form_ZtoR.cleaned_data['ZI']
                  
            ZL = complex(ZR, ZI)
            gamma = (ZL - Z0) / (ZL + Z0)

            context['form_ZtoR'] = form_ZtoR
            context['gamma_mag'] = round(math.sqrt(gamma.real*gamma.real + gamma.imag*gamma.imag), 2)
            context['gamma_ang'] = round((180/math.pi)*math.atan(gamma.imag / gamma.real), 2)
            context['form_RtoZ'] = ReflectionCoefficientToImpedanceForm()   
            return render(request, 'reflection_coeff.html', context)
    else:
        form_RtoZ = ReflectionCoefficientToImpedanceForm()
        form_ZtoR = ImpedanceToReflectionCoefficientForm()

    context['form_RtoZ'] = form_RtoZ
    context['form_ZtoR'] = form_ZtoR

    return render(request, 'reflection_coeff.html', context)