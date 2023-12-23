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

#https://github.com/andresmmera/qucs/blob/ImpedanceMatching_Update/qucs/qucs/dialogs/matchdialog.cpp#L1272

# Reference
# Microwave Engineering. David M. Pozar. 4th Edition. 2012. John Wiley and Sons

def synthesize_SingleStub_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    StubType = params['StubType']

    lambda_ = 299792458 / f0

    error = 0 # Flag for detecting forbidden impedances

    # Double stub method formulas

    Z0 = RS
    Y0 = 1. / Z0
    dl8 = lambda_ / 8
    beta = (2 * np.pi) / lambda_
    t = np.tan(beta * dl8)

    
    GL = (1 / ((RL * RL) + (XL * XL))) * RL
    BL = -(1 / ((RL * RL) + (XL * XL))) * XL
    
    


    if (GL > Y0 * ((1 + t * t) / (t * t))):
        # Not every load can be match using the double stub technique.
        error = 1


    B11 = -BL + (Y0 + np.sqrt((1 + t * t) * GL * Y0 - GL * GL * t * t)) / (t) # 1st solution
    B12 = -BL + (Y0 - np.sqrt((1 + t * t) * GL * Y0 - GL * GL * t * t)) / (t); # 2nd solution

    B21 = ((Y0 * np.sqrt((1 + t * t) * GL * Y0 - GL * GL * t * t)) + GL * Y0) / (GL * t) # 1st solution
    B22 = ((-Y0* np.sqrt((1 + t * t) * GL * Y0 - GL * GL * t * t)) + GL * Y0) / (GL * t) # 2nd solution

    # Open circuit solution
    if (StubType == 2):
        ll1 = (np.arctan(B11 * Z0)) / (2 * np.pi)
        ll2 = (np.arctan(B21 * Z0)) / (2 * np.pi)
        if (ll1 < 0):
            ll1 = ll1 + 0.5
        if (ll2 < 0):
            ll2 = ll2 + 0.5

    else:# Short
        B1 = -BL - (Y0+np.sqrt((1+t*t)*GL*Y0) - GL*GL*t*t)/(t)
        B2 = -(Y0*np.sqrt(Y0*GL*(1+t*t) - GL*GL*t*t) + GL*Y0)/(GL*t)
        ll1 = -(1/(2*np.pi))*np.arctan(1/(B1*Z0))
        ll2 = -(1/(2*np.pi))*np.arctan(1/(B2*Z0))
        dl8 *= 3
 


    # Convert distance to degrees
    ll1 = 360*f0*ll1*lambda_/299792458
    if (ll1 < 0):
        ll1 = ll1 + 90

    dl8 = 360*f0*dl8/299792458
    ll2 = 360*f0*ll2*lambda_/299792458
    if (ll2 < 0):
        ll2 = ll2 + 90

    return ll2, dl8, ll1


def DoubleStub_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    StubType = params['StubType']
    w0 = 2*np.pi*f0

    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']
    
    
       
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    [ll2, dl8, ll1] = synthesize_SingleStub_Matching_Network(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'DoubleStub' + str(int(StubType))
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

    # 1st Stub
    # Drawing
    d += TransmissionLine().down().label("Z\u2080 = " + str(RS) + " \u03A9\nl = " + str(round(ll2, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').linewidth(1)
    if (StubType == 1): # Short
        comp_val['SC1_Z0'] = RS
        comp_val['SC1_ang'] = ll2

        d += elm.Ground().linewidth(1)
    else:
        comp_val['OC1_Z0'] = RS
        comp_val['OC1_ang'] = ll2
    
    d.pop()

    d += elm.Line().right().length(1).linewidth(1)

    # Line
    # Drawing
    d += TransmissionLine().right().label("l = " + str(round(dl8, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    comp_val['TL_Z0'] = RS
    comp_val['TL_ang'] = dl8

    d.push()

    # 2nd Stub
    # Drawing
    d += TransmissionLine().down().label("Z\u2080 = " + str(RS) + " \u03A9\nl = " + str(round(ll1, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').linewidth(1)
    if (StubType == 1): # Short
        comp_val['SC2_Z0'] = RS
        comp_val['SC2_ang'] = ll1

        d += elm.Ground().linewidth(1)
    else:
        comp_val['OC2_Z0'] = RS
        comp_val['OC2_ang'] = ll1
    
    d.pop()


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val