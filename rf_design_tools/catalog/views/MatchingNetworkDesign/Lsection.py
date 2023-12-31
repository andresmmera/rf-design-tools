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

def LTspice_Lsection(params):

    data = Design_L_Section(params)
    
    LTspiceSchematic = 'Version 4\nSHEET 1 1200 400\n'
    
    # Source
    LTspiceSchematic += 'WIRE 208 0 0 0\n'
    LTspiceSchematic += 'WIRE 0 64 0 0\n'
    LTspiceSchematic += 'WIRE 0 208 0 144\n'


    LTspiceSchematic += 'SYMBOL voltage 0 48 R0\n'
    LTspiceSchematic += 'WINDOW 123 40 48 Left 2\n'
    LTspiceSchematic += 'WINDOW 39 39 77 Left 2\n'
    LTspiceSchematic += 'SYMATTR Value2 AC 1 0\n'
    LTspiceSchematic += 'SYMATTR SpiceLine Rser=50.00\n'
    LTspiceSchematic += 'SYMATTR InstName V1\n'
    LTspiceSchematic += 'SYMATTR Value \"\"\n'
    LTspiceSchematic += 'FLAG 0 208 0\n'

    if ('P' in data["topology"][0]):
        # First shunt
        if (data["topology"][0] == 'CP'):
            LTspiceSchematic += 'SYMBOL cap 192 64 R0\n'
            LTspiceSchematic += 'SYMATTR InstName C1\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][0], 'Capacitance').replace(" ", "").replace("F", "") +'\n'

            LTspiceSchematic += 'WIRE 208 64 208 0\n'
            LTspiceSchematic += 'WIRE 208 208 208 128\n'
            LTspiceSchematic += 'FLAG 208 208 0\n'
        else:
            # Shunt inductor
            LTspiceSchematic += 'SYMBOL ind 192 64 R0\n'
            LTspiceSchematic += 'SYMATTR InstName L1\n'
            LTspiceSchematic += 'WINDOW 3 74 55 VTop 2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][0], 'Inductance').replace(" ", "").replace("H", "") +'\n'
            LTspiceSchematic += 'FLAG 208 208 0\n'
            LTspiceSchematic += 'WIRE 208 80 208 0\n'
            LTspiceSchematic += 'WIRE 208 208 208 160\n'
            
    else:
        # First series

        if (data["topology"][0] == 'CS'):
            # Series capacitor
            LTspiceSchematic += 'SYMBOL cap 336 -16 R90\n'
            LTspiceSchematic += 'SYMATTR InstName C1\n'
            LTspiceSchematic += 'WINDOW 0 0 32 VBottom 2\n'
            LTspiceSchematic += 'WINDOW 3 32 32 VTop 2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][0], 'Capacitance').replace(" ", "").replace("F", "") +'\n'
            LTspiceSchematic += 'WIRE 272 0 208 0\n'
            LTspiceSchematic += 'WIRE 400 0 336 0\n'
        else:
            # Series inductor
            LTspiceSchematic += 'SYMBOL ind 256 16 R270\n'
            LTspiceSchematic += 'SYMATTR InstName L1\n'
            LTspiceSchematic += 'WINDOW 0 32 56 VTop 2\n'
            LTspiceSchematic += 'WINDOW 3 5 56 VBottom 2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][0], 'Inductance').replace(" ", "").replace("H", "") +'\n'
            LTspiceSchematic += 'WIRE 272 0 208 0\n'
            LTspiceSchematic += 'WIRE 400 0 352 0\n'

    if ('P' in data["topology"][1]):
        # Last shunt
        if (data["topology"][1] == 'CP'):
            LTspiceSchematic += 'SYMBOL cap 384 64 R0\n'
            LTspiceSchematic += 'SYMATTR InstName C2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][1], 'Capacitance').replace(" ", "").replace("F", "") +'\n'
            LTspiceSchematic += 'FLAG 400 208 0\n'
            LTspiceSchematic += 'WIRE 400 64 400 0\n'
            LTspiceSchematic += 'WIRE 400 208 400 128\n'
        else:
            # Shunt inductor
            LTspiceSchematic += 'SYMBOL ind 384 64 R0\n'
            LTspiceSchematic += 'SYMATTR InstName L2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][1], 'Inductance').replace(" ", "").replace("H", "") +'\n'
            LTspiceSchematic += 'FLAG 400 208 0\n'

            LTspiceSchematic += 'WIRE 400 80 400 0\n'
            LTspiceSchematic += 'WIRE 400 208 400 160\n'

    else:
        # Last series
        if (data["topology"][1] == 'CS'):
            # Series capacitor
            LTspiceSchematic += 'WINDOW 3 32 32 VTop 2\n'
            LTspiceSchematic += 'SYMBOL cap 336 -16 R90\n'
            LTspiceSchematic += 'WINDOW 0 0 32 VBottom 2\n'
            LTspiceSchematic += 'WINDOW 3 32 32 VTop 2\n'
            LTspiceSchematic += 'SYMATTR InstName C2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][1], 'Capacitance').replace(" ", "").replace("F", "") +'\n'
            LTspiceSchematic += 'WIRE 272 0 208 0\n'
            LTspiceSchematic += 'WIRE 400 0 336 0\n'
        else:
            # Series inductor
            LTspiceSchematic += 'SYMBOL ind 256 16 R270\n'
            LTspiceSchematic += 'WINDOW 0 32 56 VTop 2\n'
            LTspiceSchematic += 'WINDOW 3 5 56 VBottom 2\n'
            LTspiceSchematic += 'SYMATTR InstName L2\n'
            LTspiceSchematic += 'SYMATTR Value '+ getUnitsWithScale(data["values_network"][1], 'Inductance').replace(" ", "").replace("H", "") +'\n'
            LTspiceSchematic += 'WIRE 272 0 208 0\n'
            LTspiceSchematic += 'WIRE 400 0 352 0\n'

    # Load
    LTspiceSchematic += 'WIRE 592 0 400 0\n'
    LTspiceSchematic += 'WIRE 592 80 592 0\n'
    LTspiceSchematic += 'WIRE 592 224 592 160\n'

    # Resistive part
    RL = params['RL']
    XL = params['XL']
    if (params['XL'] != 0):
        Rp = (RL*RL + XL*XL)/RL
        XL = (RL*RL + XL*XL)/XL
        RL = Rp
        w = 2*np.pi*params['f0']
        LTspiceSchematic += 'RECTANGLE Normal 880 256 544 -48 2\n'
        LTspiceSchematic += 'TEXT 536 -88 Left 2 ;' + str(params['RL']) + '+j' + str(params['XL']) +'Ohm @ '+ str(params["f0"]*1e-6)+'MHz\n'
        if (XL < 0):
            # Capacitor
            C = -1/(w*XL)
            LTspiceSchematic += 'SYMBOL cap 720 96 R0\n'
            LTspiceSchematic += 'SYMATTR InstName XC\n'
            LTspiceSchematic += 'SYMATTR Value ' + getUnitsWithScale(C, 'Capacitance').replace(" ", "").replace("H", "") + '\n'
            LTspiceSchematic += 'WIRE 736 0 592 0\n'
            LTspiceSchematic += 'WIRE 736 96 736 0\n'
            LTspiceSchematic += 'WIRE 736 224 736 160\n'
            LTspiceSchematic += 'FLAG 736 224 0\n'
        else:
            # Inductor
            L = XL/w
            LTspiceSchematic += 'SYMBOL ind 720 64 R0\n'
            LTspiceSchematic += 'SYMATTR InstName XL\n'
            LTspiceSchematic += 'SYMATTR Value ' + getUnitsWithScale(L, 'Inductance').replace(" ", "").replace("H", "") + '\n'
            LTspiceSchematic += 'FLAG 736 224 0\n'
            LTspiceSchematic += 'WIRE 736 0 592 0\n'
            LTspiceSchematic += 'WIRE 736 80 736 0\n'
            LTspiceSchematic += 'WIRE 736 224 736 160\n'

    LTspiceSchematic += 'SYMBOL res 576 64 R0\n'
    LTspiceSchematic += 'SYMATTR InstName RL\n'
    LTspiceSchematic += 'SYMATTR Value ' + str(params['RL']) + '\n'
    LTspiceSchematic += 'FLAG 592 224 0\n'
   
    LTspiceSchematic += 'TEXT 0 280 Left 2 !.ac lin 1001 '+ str(params['f_start']*1e-6) + 'Meg ' + str(params['f_stop']*1e-6) +'Meg\n'
    LTspiceSchematic += 'TEXT 0 320 Left 2 !.net I(RL) V1'

    filename = 'L-section_' + params['Mask'] + '_RS_' + str(params['RS']) + '_Ohm_' +  'RL_' + str(params['RL']) + '_j' + str(params['XL']) + '.asc'
    return LTspiceSchematic, filename