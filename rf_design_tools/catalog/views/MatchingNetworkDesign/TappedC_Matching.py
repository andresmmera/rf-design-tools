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


def synthesize_Tapped_C_Transformer_MatchingNetwork(params):

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
    L = RS / (w0 * Q)
    C2 = Q2 / (RL * w0)
    C1 = C2 * (Q2 * Q2 + 1) / (Q * Q2 - Q2 * Q2)


    return L, C1, C2

def Tapped_C_Transformer_MatchingNetwork(params):

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
       
    [L, C1, C2] = synthesize_Tapped_C_Transformer_MatchingNetwork(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'Tapped-C'
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
        d += elm.Capacitor().down().label(getUnitsWithScale(C2, 'Capacitance'), fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Inductor2().down().label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    d.pop()
    d += elm.Capacitor().right().label(getUnitsWithScale(C1, 'Capacitance'), fontsize=_fontsize).linewidth(1)


    d.push()
    # 2 shunt element
    if (RL > RS):
        d += elm.Inductor2().down().label(getUnitsWithScale(L, 'Inductance'), fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Capacitor().down().label(getUnitsWithScale(C2, 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    d.pop()


    # Network
    comp_val['L'] = L
    comp_val['C1'] = C1
    comp_val['C2'] = C2


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val