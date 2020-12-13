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


################################################################################################
#
#      FORM #1 - REFLECTION COEFFICIENT
#
#
from .forms import ReflectionCoefficientToImpedanceForm, ImpedanceToReflectionCoefficientForm
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
            S11 = round(20*math.log10(gamma_mag), 2)
            gamma_ang = form_RtoZ.cleaned_data['gamma_ang']     
            gamma = complex(gamma_mag*math.cos((math.pi/180)*gamma_ang), gamma_mag*math.sin((math.pi/180)*gamma_ang))
            
            # Calculations
            ZL = Z0*(1+gamma)/(1-gamma)
            ZLR = str(round(ZL.real, 2))
            ZLI = str(round(abs(ZL.imag), 2))

            if ZL.imag > 0:
                result = ZLR + ' + j ' + ZLI
            if ZL.imag < 0:
                result = ZLR + ' - j ' + ZLI
            if abs(ZL.imag) < 1e-3:
                result = ZLR

            # Assign context for HTML processing
            context['ZL'] = result
            context['S11'] = S11

            context['form_RtoZ'] = form_RtoZ
            context['form_ZtoR'] = ImpedanceToReflectionCoefficientForm()
            return render(request, 'reflection_coeff.html', context)

        if form_ZtoR.is_valid():
            # Process ZtoR form

            # Get data from the ZtoR form
            Z0 = complex(form_ZtoR.cleaned_data['Z0'], 0)
            ZR = form_ZtoR.cleaned_data['ZR']
            ZI = form_ZtoR.cleaned_data['ZI']
                  
            # Calculations
            ZL = complex(ZR, ZI)
            gamma = (ZL - Z0) / (ZL + Z0)
            gamma_mag = round(math.sqrt(gamma.real*gamma.real + gamma.imag*gamma.imag), 2)
            S11 = round(20*math.log10(gamma_mag), 2)
            gamma_ang = round((180/math.pi)*math.atan(gamma.imag / gamma.real), 2)

            # Assign context for HTML processing
            context['gamma_mag'] = gamma_mag
            context['gamma_ang'] = gamma_ang
            context['S11'] = S11

            context['form_ZtoR'] = form_ZtoR
            context['form_RtoZ'] = ReflectionCoefficientToImpedanceForm()   
            return render(request, 'reflection_coeff.html', context)
    else:
        form_RtoZ = ReflectionCoefficientToImpedanceForm()
        form_ZtoR = ImpedanceToReflectionCoefficientForm()

    context['form_RtoZ'] = form_RtoZ
    context['form_ZtoR'] = form_ZtoR

    return render(request, 'reflection_coeff.html', context)

################################################################################################
#
#      FORM #2 - RF POWER CONVERTER
#
#

from .forms import RF_PowerConversionForm
from django.http import HttpResponse
from django.template import loader

def CalculatePowerConverterView(request):
    context = {}
    if request.method == "POST":
        #Catch the form
        form = RF_PowerConversionForm(request.POST)
        if form.is_valid():
            P = form.cleaned_data['P']
            old_units = form.cleaned_data['old_units']
            new_units = form.cleaned_data['new_units']

            # Convert the input power to W
            if old_units == '0': # From W
                power = P
            else:
                if old_units == '1': # From dBm
                    power = math.pow(10, 0.1*(P-30))
                else:
                    if old_units == '2': # From dBuV75
                        power = math.pow(10, 0.1*(P - 138.75))
                    else:
                        if old_units == '3': # From dBmV75
                            power = math.pow(10, 0.1*(P - 78.75))
                        else:
                            if old_units == '4': # From dBuV50
                                power = math.pow(10, 0.1*(P - 136.99))
                            else:
                                if old_units == '5': # From dBmV50
                                    power = math.pow(10, 0.1*(P - 76.75))
                                else:
                                    if old_units == '6': # From dBpW
                                        power = math.pow(10, 0.1*(P-120))
            
            P = power # Change the name of the variable so as to make the coding nicer

            # Convert power to the selected unit
            if new_units == '0': # To W
                power = P
            else:
                if new_units == '1': # To dBm
                    power = 10*math.log10(P) + 30
                else:
                    if new_units == '2': # To dBuV75
                        power = 10*math.log10(P) + 138.75
                    else:
                        if new_units == '3': # To dBmV75
                            power = 10*math.log10(P) + 78.75
                        else:
                            if new_units == '4': # To dBuV50
                                power = 10*math.log10(P) + 136.99
                            else:
                                if new_units =='5': # To dBmV50
                                    power = 10*math.log10(P) + 76.99
                                else:
                                    if new_units == '6': # To dBpW
                                        power = 10*math.log10(P) + 120


            context['Pnew'] = round(power, 2)
            context['new_units'] =  RF_PowerConversionForm.CHOICES_Units[int(new_units)][1]
            context['form'] = form
            return render(request, 'RF_power_converter.html', context)
    else:
        form = RF_PowerConversionForm()
    
    context['form'] = form
    return render(request, 'RF_power_converter.html', context)