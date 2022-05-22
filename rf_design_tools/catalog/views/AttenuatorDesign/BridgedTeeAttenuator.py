# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date



def Synthesize_BridgedTee_Attenuator(params):
    NetworkType, comp_val = getBridgedTeeAttenuatorNetwork(params);
    Schematic = getBridgedTeeAttenuatorSchematic(params);
    return Schematic, NetworkType, comp_val

def Design_BridgedTee_Attenuator(params):
    # Unpack the dictionary
    Pin =  params['Pin'] # dBm
    ZS = params['ZS']
    ZL = params['ZL']
    att = params['att']


    Rseries = ZS*(pow(10, 0.05*att)-1)
    Rshunt = ZS/(pow(10, 0.05*att)-1)

    Pin = pow(10, 0.1*Pin-3) # W
    Pseries = Pin*(4*Rseries*Rshunt*Rshunt*ZS)/(pow((Rseries*Rshunt+ZS*(2*Rshunt+ZS)),2))
    Pshunt = Pin*(4*Rshunt*ZS*ZS*ZS)/(pow((Rseries*Rshunt + ZS*(2*Rshunt+ZS)),2))
    PR2 = Pin*(pow((Rseries*Rshunt+ZS*ZS),2))/pow(Rseries*Rshunt+ZS*(2*Rshunt+ZS), 2)

    data = {}
    data['Rseries'] = Rseries
    data['Rshunt'] = Rshunt

    data['Pseries'] = Pseries
    data['Pshunt'] = Pshunt
    data['PR2'] = PR2


    return data


def getBridgedTeeAttenuatorNetwork(params):
    # Unpack the dictionary
    ZS = params['ZS']

    data = Design_BridgedTee_Attenuator(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Bridged-Tee'
    NetworkType['freq'] = np.linspace(params['f_start'], params['f_stop'], params['n_points'])*1e6
    comp_val['ZS'] = params['ZS']
    comp_val['ZL'] = params['ZL']
    comp_val['Rseries'] = data["Rseries"]
    comp_val['Rshunt'] = data["Rshunt"]
    comp_val['Z0'] = ZS
          
    return NetworkType, comp_val


def getBridgedTeeAttenuatorSchematic(params):

    data = Design_BridgedTee_Attenuator(params)

    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(params["ZS"]) + " \u03A9" + '\n(' + str(params['Pin']) + ' dBm)', fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)

            
    # Draw the attenuator components
    d.push()
    d += elm.Resistor().down().label(getUnitsWithScale(params["ZS"], 'Resistance') +
     '\n(' + getUnitsWithScale(data["PR2"], 'Power') + ')', fontsize=_fontsize).linewidth(1)

    d += elm.Line().right().length(1.5).linewidth(1)
    
    d += elm.Resistor().down().label(getUnitsWithScale(data["Rshunt"], 'Resistance') + 
     '\n(' + getUnitsWithScale(data["Pshunt"], 'Power') + ')', fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)
     
    d.pop()
    d += elm.Resistor().right().label(getUnitsWithScale(data["Rseries"], 'Resistance') +
     '\n(' + getUnitsWithScale(data["Pseries"], 'Power') + ')', fontsize=_fontsize).linewidth(1)
    d.push()

    d += elm.Resistor().down().label(getUnitsWithScale(params["ZS"], 'Resistance') + 
     '\n(0 uW)', fontsize=_fontsize).linewidth(1)
    d += elm.Line().left().length(1.5).linewidth(1)

    d.pop()

    # Draw the load port
    d += elm.Line().right().length(2).linewidth(1)

    d += elm.Dot().label('ZL = ' + str(params["ZL"]) + " \u03A9" + '\n(' + str(params['Pin'] - params['att']) + ' dBm)' , fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d