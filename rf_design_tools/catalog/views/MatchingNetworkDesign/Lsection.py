# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date

# Reference:
# Microwave and RF Design Networks. Steer, M. 2019. North Carolina State University Libraries. Page 177


def Synthesize_L_Section(params):
    NetworkType, comp_val = get_L_Section_Network(params);
    Schematic = get_L_Section_Schematic(params);
    return Schematic, NetworkType, comp_val

def Design_L_Section(params):
    # Unpack the dictionary
    RS =  params['RS'] # dBm
    XS = params['XS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    Mask = params['Mask']
    w0 = 2*np.pi*f0
    topology = []
    values_network = []

    if (RS > RL):
        ###############################
        #   RS -------- X ----- RL
        #         |
        #         B
        #         |
        #        ---

        if (Mask == 'Lowpass'):
            X = np.sqrt(RL * (RS - RL)) - XL
            B = np.sqrt((RS - RL) / RL) / RS
        else:
            # Highpass
            X = -np.sqrt(RL * (RS - RL)) - XL
            B = -np.sqrt((RS - RL) / RL) / RS

        # Shunt element
        if (B > 0):
            # Capacitor
            C = B/w0
            topology.append('CP')
            values_network.append(C)
        else:
            # Inductor
            L = -1/(w0*B)
            topology.append('LP')
            values_network.append(L)

        # Series element
        if (X < 0):
            # Capacitor
            C = -1 / (w0 * X)
            topology.append('CS')
            values_network.append(C)
        else:
            # Inductor
            L = X / w0
            topology.append('LS')
            values_network.append(L)
    else:
        # RS < RL
        ############################
        # RS --- X --------- RL
        #             |
        #             B
        #             |
        #            ---
        
        if (Mask == 'Lowpass'):
            B = (XL + np.sqrt(RL / RS) * np.sqrt(RL * RL + XL * XL - RS * RL)) / (RL * RL + XL * XL)
            X = 1 / B + XL * RS / RL - RS / (B * RL)
        else:
            B = (XL - np.sqrt(RL / RS) * np.sqrt(RL * RL + XL * XL - RS * RL)) / (RL * RL + XL * XL)
            X = 1 / B + XL * RS / RL - RS / (B * RL);

        # Series element
        if (X < 0): # Capacitor
            C = -1 / (w0 * X)
            topology.append('CS')
            values_network.append(C)
        else: # Inductor
            L = X / w0
            topology.append('LS')
            values_network.append(L)

        # Shunt element
        if (B > 0): # Capacitor
            C = B / w0
            topology.append('CP')
            values_network.append(C)
        else: # Inductor
            L = -1 / (w0 * B)
            topology.append('LP')
            values_network.append(L)


    data = {}
    data['ZS'] = RS + 1j*XS
    data['ZL'] = RL + 1j*XL
    data['topology'] = topology
    data['values_network'] = values_network
    
    return data


def get_L_Section_Network(params):

    data = Design_L_Section(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'L-Section'
    comp_val['ZS'] = params['RS'] + 1j*params['XS']
    comp_val['ZL'] = params['RL'] + 1j*params['XL']
    comp_val['topology'] = data["topology"]
    comp_val['values_network'] = data["values_network"]
          
    return NetworkType, comp_val


def get_L_Section_Schematic(params):

    data = Design_L_Section(params)

    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    if (params["XS"] > 0):
        d += elm.Dot().label('RS = ' + str(params["RS"]) + '+ j' + str(params('XS'))+ " \u03A9", fontsize=_fontsize).linewidth(1)
    elif (params["XS"] == 0):
        d += elm.Dot().label('RS = ' + str(params["RS"]) + " \u03A9", fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Dot().label('RS = ' + str(params["RS"]) + '- j' + str(-params('XS'))+ " \u03A9", fontsize=_fontsize).linewidth(1)
    
    d += elm.Line().length(2).linewidth(1)

            
    # Draw the matching network components
    d.push()
    for i in range(0, 2):
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

    if (params["XL"] > 0):
        d += elm.Dot().label('ZL = ' + str(params["RL"]) + '+ j' + str(params["XL"]) + " \u03A9" , fontsize=_fontsize).linewidth(1)
    elif(params["XL"] == 0):
        d += elm.Dot().label('ZL = ' + str(params["RL"]) + " \u03A9" , fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Dot().label('ZL = ' + str(params["RL"]) + '- j' + str(-params["XL"] ) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d