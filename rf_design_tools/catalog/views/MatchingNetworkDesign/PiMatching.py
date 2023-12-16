# Copyright 2020-2023 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date

def synthesize_Pi_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    Q = params['Q']
    PiTee_NetworkMask = params['PiTee_NetworkMask']

    Rv = max(RS, RL)/(Q*Q + 1) # Rb is always smaller than RS and RL

    # There are four possible networks for Pi-matching


    # First section
    
    ###############################
    #   RS -------- X ----- Rv
    #         |
    #         B
    #         |
    #        ---
    
    # Lowpass
    X1_LP = np.sqrt(Rv * (RS - Rv)) # XL is 0 since Rv is real
    B1_LP = np.sqrt((RS - Rv) / Rv) / RS

    # Highpass
    X1_HP = -np.sqrt(Rv * (RS - Rv)) # XL is 0 since Rv is real
    B1_HP = -np.sqrt((RS - Rv) / Rv) / RS


    # Second section
    
    ###############################
    # Rv --- X --------- ZL
    #             |
    #             B
    #             |
    #            ---

    # Lowpass
    B2_LP = (XL + np.sqrt(RL / Rv) * np.sqrt(RL * RL + XL * XL - Rv * RL)) / (RL * RL + XL * XL)
    X2_LP = 1 / B2_LP + XL * Rv / RL - Rv / (B2_LP * RL)

    # Highpass
    B2_HP = (XL - np.sqrt(RL / Rv) * np.sqrt(RL * RL + XL * XL - Rv * RL)) / (RL * RL + XL * XL)
    X2_HP = 1 / B2_HP + XL * Rv / RL - Rv / (B2_HP * RL);

    if PiTee_NetworkMask == 1:
        # 1st combination: 1st LP, 2nd LP

        #   RS -------- X1_LP ----- Rv --- X2_LP --------- ZL
        #         |                                 |
        #       B1_LP                             B2_LP
        #         |                                 |
        #        ---                               ---

        B1 = B1_LP
        X1 = X1_LP + X2_LP
        B2 = B2_LP

    elif PiTee_NetworkMask == 2:
        # 2 nd combination: 1st LP, 2nd HP

        #   RS -------- X1_LP ----- Rv --- X2_HP --------- ZL
        #         |                                 |
        #       B1_LP                             B2_HP
        #         |                                 |
        #        ---                               ---
    
        B1 = B1_LP
        X1 = X1_LP + X2_HP
        B2 = B2_HP

    elif PiTee_NetworkMask == 3:
        # 3rd combination: 1st HP, 2nd LP

        #   RS -------- X1_HP ----- Rv --- X2_LP --------- ZL
        #         |                                 |
        #       B1_HP                             B2_LP
        #         |                                 |
        #        ---                               ---

        B1 = B1_HP
        X1 = X1_HP + X2_LP
        B2 = B2_LP

    elif PiTee_NetworkMask == 4:
        # 4th combination: 1st HP, 2nd HP

        #   RS -------- X1_HP ----- Rv --- X2_HP --------- ZL
        #         |                                 |
        #       B1_HP                             B2_HP
        #         |                                 |
        #        ---                               ---

        B1 = B1_HP
        X1 = X1_HP + X2_HP
        B2 = B2_HP


    return B1, X1, B2


def Pi_MatchingNetwork(params):

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

    

    [B1, X1, B2] = synthesize_Pi_Matching_Network(params)

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

    # First shunt element
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

    # Series element
    d.pop()
    if (X1 < 0): # Capacitor
        C = -1 / (w0 * X1)

        # Schematic
        d += elm.Capacitor().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_C += 1
        x.append(C)
        topology.append("CS")

    else: # Inductor
        L = X1 / w0
        
        # Schematic
        d += elm.Inductor2(loops=2).label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)
        
        # Network
        count_L += 1
        x.append(L)
        topology.append("LS")


    d.push()
    # Second shunt element
    if (B2 > 0): # Capacitor
        C = B2 / w0

        # Schematic
        d += elm.Capacitor().down().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_C += 1
        x.append(C)
        topology.append("CP")

    else: # Inductor
        L = -1 / (w0 * B2)

        # Schematic
        d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_L += 1
        x.append(L)
        topology.append("LP")

    d += elm.Ground().linewidth(1)

    
    d.pop()
        
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