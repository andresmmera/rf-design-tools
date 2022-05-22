# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date



def Synthesize_Pi_Attenuator(params):
    NetworkType, comp_val = getPiAttenuatorNetwork(params);
    Schematic = getPiAttenuatorSchematic(params);



    return Schematic, NetworkType, comp_val

def Design_Pi_Attenuator(params):
    # Unpack the dictionary
    Pin =  params['Pin'] # dBm
    ZS = params['ZS']
    ZL = params['ZL']
    att = params['att']


    Rseries = 0.5*(pow(10, 0.1*att) - 1)*np.sqrt((ZS*ZL)/(pow(10, 0.1*att)))
    Rshunt1 = 1 / (((pow(10, 0.1*att) + 1) / (ZS * (pow(10, 0.1*att) - 1))) - (1 / Rseries))
    Rshunt2 = 1 / (((pow(10, 0.1*att) + 1) / (ZL * (pow(10, 0.1*att) - 1))) - (1 / Rseries))

    Pin = pow(10, 0.1*Pin-3) # mW
    Pshunt1 = Pin*ZS/Rshunt1
    Pseries = Pin*(Rseries*pow((Rshunt1-ZS), 2))/(Rshunt1*Rshunt1*ZS)
    Pshunt2 = Pin*(pow(Rshunt1*Rseries - ZS*(Rshunt1+Rseries),2))/(Rshunt1*Rshunt1*Rshunt2*ZS)

    data = {}
    data['Rshunt1'] = Rshunt1
    data['Rseries'] = Rseries
    data['Rshunt2'] = Rshunt2

    data['Pshunt1'] = Pshunt1
    data['Pseries'] = Pseries
    data['Pshunt2'] = Pshunt2


    return data


def getPiAttenuatorNetwork(params):
    # Unpack the dictionary
    data = Design_Pi_Attenuator(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Pi'
    NetworkType['freq'] = np.linspace(params['f_start'], params['f_stop'], params['n_points'])*1e6
    comp_val['ZS'] = params['ZS']
    comp_val['ZL'] = params['ZL']
    comp_val['Rshunt1'] = data["Rshunt1"]
    comp_val['Rseries'] = data["Rseries"]
    comp_val['Rshunt2'] = data["Rshunt2"]
    return NetworkType, comp_val


def getPiAttenuatorSchematic(params):

    data = Design_Pi_Attenuator(params)

    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(params["ZS"]) + " \u03A9" + '\n(' + str(params['Pin']) + ' dBm)', fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)

            
    # Draw the filter components
    d.push()
    d += (R1 := elm.Resistor().down().label(getUnitsWithScale(data["Rshunt1"], 'Resistance') +
     '\n(' + getUnitsWithScale(data["Pshunt1"], 'Power') + ')', fontsize=_fontsize).linewidth(1))

    d += elm.Ground().linewidth(1)
    d.pop()
    d += elm.Resistor().right().label(getUnitsWithScale(data["Rseries"], 'Resistance') + 
     '\n(' + getUnitsWithScale(data["Pseries"], 'Power') + ')', fontsize=_fontsize).linewidth(1)
     
    d.push()
    d += elm.Resistor().down().label(getUnitsWithScale(data["Rshunt2"], 'Resistance') + 
     '\n(' + getUnitsWithScale(data["Pshunt2"], 'Power') + ')', fontsize=_fontsize, loc='bottom').linewidth(1)
    d += elm.Ground().linewidth(1)
    d.pop()

    # Draw the load port
    d += elm.Line().right().length(2).linewidth(1)

    d += elm.Dot().label('ZL = ' + str(params["ZL"]) + " \u03A9" + '\n(' + str(params['Pin'] - params['att']) + ' dBm)' , fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d