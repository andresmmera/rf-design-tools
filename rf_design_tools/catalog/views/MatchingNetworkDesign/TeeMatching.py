# Copyright 2020-2023 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date

def synthesize_Tee_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    Q = params['Q']
    PiTee_NetworkMask = params['PiTee_NetworkMask']

    Rv = (Q*Q + 1)*min(RS, RL) # Rb is always smaller than RS and RL

    # There are four possible networks for Tee-matching


    # First section
    
    ###############################
    #   RS -------- X -------- Rv
    #                    |
    #                    B
    #                    |
    #                   ---
    
    # Lowpass
    B1_LP = (np.sqrt(Rv / RS) * np.sqrt(Rv * Rv - RS * Rv)) / (Rv * Rv) # XL = 0 as Rv is pure real
    X1_LP = 1 / B1_LP + RS / Rv - RS / (B1_LP * Rv)

    # Highpass
    B1_HP = (-np.sqrt(Rv / RS) * np.sqrt(Rv * Rv - RS * Rv)) / (Rv * Rv)
    X1_HP = 1 / B1_HP + RS / Rv - RS / (B1_HP * Rv);


    # Second section
    
    ###############################
    # Rv ------------ X ----- ZL
    #       |
    #       B
    #       |
    #      ---

    # Lowpass
    X2_LP = np.sqrt(RL * (Rv - RL)) - XL
    B2_LP = np.sqrt((Rv - RL) / RL) / Rv

    # Highpass
    X2_HP = -np.sqrt(RL * (Rv - RL)) - XL
    B2_HP = -np.sqrt((Rv - RL) / RL) / Rv

    if PiTee_NetworkMask == 1:
        # 1st combination: 1st LP, 2nd LP

        #   RS ----- X1_LP ---------- Rv ------------ X2_LP --------- ZL
        #                      |              |
        #                    B1_LP          B2_LP
        #                      |              |
        #                     ---            ---

        X1 = X1_LP
        B1 = B1_LP + B2_LP
        X2 = X2_LP

    elif PiTee_NetworkMask == 2:
        # 2 nd combination: 1st LP, 2nd HP

        #   RS ----- X1_LP ---------- Rv ------------ X2_HP --------- ZL
        #                      |              |
        #                    B1_LP          B2_HP
        #                      |              |
        #                     ---            ---
    
        X1 = X1_LP
        B1 = B1_LP + B2_HP
        X2 = X2_HP

    elif PiTee_NetworkMask == 3:
        # 3rd combination: 1st HP, 2nd LP

        #   RS ----- X1_HP ---------- Rv ------------ X2_LP --------- ZL
        #                      |              |
        #                    B1_HP          B2_LP
        #                      |              |
        #                     ---            ---
    
        X1 = X1_HP
        B1 = B1_HP + B2_LP
        X2 = X2_LP

    elif PiTee_NetworkMask == 4:
        # 4th combination: 1st HP, 2nd HP

        #   RS ----- X1_HP ---------- Rv ------------ X2_HP --------- ZL
        #                      |              |
        #                    B1_HP          B2_HP
        #                      |              |
        #                     ---            ---
    
        X1 = X1_HP
        B1 = B1_HP + B2_HP
        X2 = X2_HP

    return X1, B1, X2


def Tee_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    w0 = 2*np.pi*f0

    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']
    
    
       
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    # Component counter
    count_C = 0
    count_L = 0

    

    [X1, B1, X2] = synthesize_Tee_Matching_Network(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Pi'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL + 1j*XL
    
    x = []
    topology = []

        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    d.push()

    # First series element
    if (X1 < 0):
        # Capacitor
        C = -1 / (w0 * X1)

        # Schematic
        d += elm.Capacitor().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_C += 1
        x.append(C)
        topology.append("CS")
    else:
        # Inductor
        L = X1 / w0
        
        # Schematic
        d += elm.Inductor2(loops=2).label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)
        
        # Network
        count_L += 1
        x.append(L)
        topology.append("LS")

    d.push()
    
    # Shunt element

    if (B1 > 0): # Capacitor
        C = B1 / w0

        # Schematic
        d += elm.Capacitor().down().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_C += 1
        x.append(C)
        topology.append("CP")

    else: # Inductor
        L = -1 / (w0 * B1)

        # Schematic
        d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_L += 1
        x.append(L)
        topology.append("LP")

    d += elm.Ground().linewidth(1)
    
    d.pop()

    # Second series element
    if (X2 < 0):
        # Capacitor
        C = -1 / (w0 * X2)

        # Schematic
        d += elm.Capacitor().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_C += 1
        x.append(C)
        topology.append("CS")
    else:
        # Inductor
        L = X2 / w0
        
        # Schematic
        d += elm.Inductor2(loops=2).label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)
        
        # Network
        count_L += 1
        x.append(L)
        topology.append("LS")

        
    # Drawing
    d += elm.Line().length(1).linewidth(1)
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    comp_val['values'] = x
    comp_val['topology'] = topology

       
    return d, NetworkType, comp_val