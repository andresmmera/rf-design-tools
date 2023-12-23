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

# Reference
# Fundamentals of RF and Microwave Transistor Amplifiers. Inder J. Bahl. Wiley. 2009. Pg 157

def synthesize_L4_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']

    lambda_ = 299792458 / f0

    Zm = np.sqrt(RS*RL)

 


    l4 = 90
    l8 = 45

    return Zm, l4

def L4_MatchingNetwork(params):

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
       
    [Zm, l4] = synthesize_L4_Matching_Network(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'L4'
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
    

    # lambda/4 line
    # Drawing
    d += TransmissionLine().right().label("l = " + str(round(l4, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(round(Zm,1)) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)


    # Network
    comp_val['Zm'] = Zm


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val