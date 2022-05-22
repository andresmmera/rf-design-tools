# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *


# Import for the generation of the Qucs schematic
from datetime import date



def Synthesize_Tee_Attenuator(params):
    NetworkType, comp_val = getTeeAttenuatorNetwork(params);
    Schematic = getTeeAttenuatorSchematic(params);
    return Schematic, NetworkType, comp_val

def Design_Tee_Attenuator(params):
    # Unpack the dictionary
    Pin =  params['Pin'] # dBm
    ZS = params['ZS']
    ZL = params['ZL']
    att = params['att']


    Rshunt = 2 * (np.sqrt(ZS*ZL*pow(10, 0.1*att)))/(pow(10, 0.1*att) - 1)
    Rseries1 = ZS * (pow(10, 0.1*att) + 1)/(pow(10, 0.1*att) - 1) - Rshunt
    Rseries2 = ZL * (pow(10, 0.1*att) + 1)/(pow(10, 0.1*att) - 1) - Rshunt

    Pin = pow(10, 0.1*Pin-3) # mW
    Pseries1 = Pin*Rseries1/ZS
    Pshunt = Pin*(Rseries1 - ZS)*(Rseries1 - ZS)/(Rshunt*ZS)
    Pseries2 = Pin*(Rseries2*(Rseries1+Rshunt-ZS)*(Rseries1+Rshunt-ZS))/(ZS*Rshunt*Rshunt)

    data = {}
    data['Rseries1'] = Rseries1
    data['Rshunt'] = Rshunt
    data['Rseries2'] = Rseries2

    data['Pseries1'] = Pseries1
    data['Pshunt'] = Pshunt
    data['Pseries2'] = Pseries2


    return data


def getTeeAttenuatorNetwork(params):
    data = Design_Tee_Attenuator(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Tee'
    NetworkType['freq'] = np.linspace(params['f_start'], params['f_stop'], params['n_points'])*1e6
    comp_val['ZS'] = params['ZS']
    comp_val['ZL'] = params['ZL']
    comp_val['Rseries1'] = data["Rseries1"]
    comp_val['Rshunt'] = data["Rshunt"]
    comp_val['Rseries2'] = data["Rseries2"]
    
    return NetworkType, comp_val


def getTeeAttenuatorSchematic(params):

    data = Design_Tee_Attenuator(params)

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
    d += (R1 := elm.Resistor().right().label(getUnitsWithScale(data["Rseries1"], 'Resistance') +
     '\n(' + getUnitsWithScale(data["Pseries1"], 'Power') + ')', fontsize=_fontsize).linewidth(1))
    d.push()

    d += elm.Resistor().down().label(getUnitsWithScale(data["Rshunt"], 'Resistance') + 
     '\n(' + getUnitsWithScale(data["Pshunt"], 'Power') + ')', fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)
     
    d.pop()
    d += elm.Resistor().right().label(getUnitsWithScale(data["Rseries2"], 'Resistance') + 
     '\n(' + getUnitsWithScale(data["Pseries2"], 'Power') + ')', fontsize=_fontsize).linewidth(1)


    # Draw the load port
    d += elm.Line().right().length(2).linewidth(1)

    d += elm.Dot().label('ZL = ' + str(params["ZL"]) + " \u03A9" + '\n(' + str(params['Pin'] - params['att']) + ' dBm)' , fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d