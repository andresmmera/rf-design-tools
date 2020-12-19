################################################################################################
#
#      FORM #2 - RF POWER CONVERTER
#
#

from catalog.forms import RF_PowerConversionForm
from django.http import HttpResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import render
from catalog.models import Tool
import math

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
    return render(request, 'RF_Power_Converter/tool/RF_power_converter.html', context)