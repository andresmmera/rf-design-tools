# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date



def Synthesize_Lumped_Line_Section(params):
    NetworkType, comp_val = get_Lumped_Line_Network(params);
    Schematic = get_Lumped_Line_Schematic(params);
    return Schematic, NetworkType, comp_val

def Design_Lumped_Line(params):
    # Unpack the dictionary
    Z0 =  params['Z0']
    f0 = params['f0']
    Mask = params['Mask']
    Structure = params['Structure']
    length = params['length']
    topology = []
    values_network = []

    c0 = 299792458;
    lambda_ = c0/f0;
    w0 = 2*np.pi*f0;
    beta  =2*np.pi/lambda_;
    length=length*lambda_;


    if (Mask == "Lowpass"): 
        if (length > lambda_/2): #Ensure length < lambda / 2
            length = length - lambda_/2;

        if (Structure == 'Pi-Type'):
            # Lowpass Pi
            L = Z0*np.sin(beta*length)/w0;
            C = (1 - np.cos(beta*length))/(w0*Z0*np.sin(beta*length));

            # Capacitor
            topology.append('CP')
            values_network.append(C)

            # Inductor
            topology.append('LS')
            values_network.append(L)

            # Capacitor
            topology.append('CP')
            values_network.append(C)

        else:
            # Lowpass T
            L = (Z0*(1-np.cos(beta*length)))/(w0*np.sin(beta*length));
            C = np.sin(beta*length)/(Z0*w0);

            # Inductor
            topology.append('LS')
            values_network.append(L)

            # Capacitor
            topology.append('CP')
            values_network.append(C)

            # Capacitor
            topology.append('LS')
            values_network.append(L)
        
    else:
        # Highpass 
        if (length < lambda_/2): #Ensure length > lambda / 2
            length = length + lambda_/2;

        if (Structure == 'Pi-Type'):
            C = -1/(w0*Z0*np.sin(beta*length));
            L = Z0*np.sin(beta*length)/(w0*(np.cos(beta*length)-1));

            # Inductor
            topology.append('LP')
            values_network.append(L)

            # Capacitor
            topology.append('CS')
            values_network.append(C)

            # Capacitor
            topology.append('LP')
            values_network.append(L)

        else:
            C = (np.sin(beta*length))/(Z0*w0*(np.cos(beta*length)-1));
            L = -Z0/(w0*np.sin(beta*length));

            # Inductor
            topology.append('CS')
            values_network.append(C)

            # Capacitor
            topology.append('LP')
            values_network.append(L)

            # Capacitor
            topology.append('CS')
            values_network.append(C)

    data = {}
    data['ZS'] = 50
    data['ZL'] = Z0*Z0/50
    data['topology'] = topology
    data['values_network'] = values_network
    
    return data


def get_Lumped_Line_Network(params):

    data = Design_Lumped_Line(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Lumped Line'
    comp_val['ZS'] = 50
    comp_val['ZL'] = np.round(data['ZL'] ,1)
    comp_val['topology'] = data["topology"]
    comp_val['values_network'] = data["values_network"]
          
    return NetworkType, comp_val


def get_Lumped_Line_Schematic(params):

    data = Design_Lumped_Line(params)

    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label(str(50) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)

    # Draw the matching network components
    d.push()
    for i in range(0, 3):
        print(data["topology"][i] + ': ' + str(data['values_network'][i]))
        if (data["topology"][i] == 'CS'):
            d += elm.Capacitor().right().label(getUnitsWithScale(data['values_network'][i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        elif(data["topology"][i] == 'LS'):
            d += elm.Inductor2().right().label(getUnitsWithScale(data['values_network'][i], 'Inductance'), fontsize=_fontsize).linewidth(1)
        elif(data["topology"][i] == 'CP'):
            d.push()
            d += elm.Capacitor().down().label(getUnitsWithScale(data['values_network'][i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            d.pop()
        elif(data["topology"][i] == 'LP'):
            d.push()
            d += elm.Inductor2().down().label(getUnitsWithScale(data['values_network'][i], 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            d.pop()

    # Draw the load port
    d += elm.Line().right().length(2).linewidth(1)

    d += elm.Dot().label(str(np.round(data["ZL"],1)) + " \u03A9" , fontsize=_fontsize).linewidth(1)

    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d