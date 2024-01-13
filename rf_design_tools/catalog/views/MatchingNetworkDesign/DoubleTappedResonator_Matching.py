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


def synthesize_DoubleTappedResonator_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    Q = params['Q']
    f0 = params['f0']
    L2 = params['Ltap']

    w0 = 2 * np.pi * f0

    # Design equations
    L1 = RS / (w0 * Q);
    Qsq = Q * Q;
    Q2 = np.sqrt((RL / RS) * (Qsq + 1) - 1);
    Leq = ((L1 * Qsq) / (1 + Qsq)) + L2;
    Ceq = 1 / (w0 * w0 * Leq);
    C2 = Q2 / (w0 * RL);
    C2_ = C2 * (1 + Q2 * Q2) / (Q2 * Q2);
    C1 = (Ceq * C2_) / (C2_ - Ceq);


    return L1, L2, C1, C2

def DoubleTappedResonator_MatchingNetwork(params):

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
       
    [L1, L2, C1, C2] = synthesize_DoubleTappedResonator_MatchingNetwork(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'DoubleTappedResonator'
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
    d += elm.Inductor2().down().label(getUnitsWithScale(L1, 'Inductance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    d.pop()
    d += elm.Inductor2().right().label(getUnitsWithScale(L2, 'Inductance'), fontsize=_fontsize).linewidth(1)
    d += elm.Capacitor().right().label(getUnitsWithScale(C1, 'Capacitance'), fontsize=_fontsize).linewidth(1)


    d.push()
    # 2 shunt element
    d += elm.Capacitor().down().label(getUnitsWithScale(C2, 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    d.pop()


    # Network
    comp_val['LP'] = L1
    comp_val['LS'] = L2
    comp_val['CS'] = C1
    comp_val['CP'] = C2


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val