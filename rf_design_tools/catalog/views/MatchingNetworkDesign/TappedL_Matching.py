# Copyright 2020-2023 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date
from ..components import TransmissionLine


def synthesize_Tapped_L_Transformer_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    Q = params['Q']
    f0 = params['f0']

    w0 = 2 * np.pi * f0

    if (RL > RS):
       aux = RL
       RL = RS
       RS = aux

    Q2 = np.sqrt((RL / RS) * (Q * Q + 1) - 1)
    C = Q / (w0 * RS)
    L2 = RL / (Q2 * w0)
    L1 = L2 * (Q * Q2 - Q2 * Q2) / (Q2 * Q2 + 1)


    return C, L1, L2

def Tapped_L_Transformer_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']

    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']  
       
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    [C, L1, L2] = synthesize_Tapped_L_Transformer_MatchingNetwork(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'Tapped-L'
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL + 1j*XL
    comp_val['f0'] = f0
    
    x = []
    topology = []

        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
   
    d.push()
    # 1st shunt element
    if (RL > RS):
        d += elm.Inductor2().down().label(getUnitsWithScale(L2, 'Inductance'), fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Capacitor().down().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    d.pop()
    d += elm.Inductor2().right().label(getUnitsWithScale(L1, 'Inductance'), fontsize=_fontsize).linewidth(1)


    d.push()
    # 2 shunt element
    if (RL > RS):
        d += elm.Capacitor().down().label(getUnitsWithScale(C, 'Capacitance'), fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Inductor2().down().label(getUnitsWithScale(L2, 'Inductance'), fontsize=_fontsize).linewidth(1)

    d += elm.Ground().linewidth(1)

    d.pop()


    # Network
    comp_val['C'] = C
    comp_val['L1'] = L1
    comp_val['L2'] = L2


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val