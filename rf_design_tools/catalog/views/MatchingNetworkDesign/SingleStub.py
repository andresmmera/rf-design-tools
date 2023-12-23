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
# Microwave Engineering. David M. Pozar. 4th Edition. 2012. John Wiley and Sons


def synthesize_SingleStub_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    f0 = params['f0']
    StubType = params['StubType']

    lambda_ = 299792458 / f0

    if (RL == RS):
        t = -XL/(2*RS)
        if (t < 0):
            dl = (np.pi + np.arctan(t)) / (2 * np.pi)
        else:
            dl = (np.arctan(t)) / (2 * np.pi)

        B = (RL * RL * t - (RS - XL * t) * (RS * t + XL))/(RS * (RL * RL + (RS * t + XL) * (RS * t + XL)))

        if (t != 0):
            d = dl * lambda_
            if (StubType == 2):
                ll = -(np.arctan(B * RS)) / (2 * np.pi)
            else:
                ll = (np.arctan(1. / (B * RS))) / (2 * np.pi)

            if ((StubType == 2) and (l1 < 0)):
                l1 = l1 + 0.5
            if ((StubType == 1) and (l1 > 0.5)):
                l1 = l1 - 0.5

            lstub = l1 * lambda_

    else:
        t1 = (XL + np.sqrt(RL*((RS-RL)*(RS-RL) + XL*XL)/RS))/(RL-RS)
        if (t1 < 0):
            dl1 = (np.pi + np.arctan(t1)) / (2 * np.pi)
        else:
            dl1 = (np.arctan(t1)) / (2 * np.pi)
        B1 = (RL * RL * t1 - (RS - XL * t1) * (RS * t1 + XL)) / (RS * (RL * RL + (RS * t1 + XL) * (RS * t1 + XL)));
    
        t2 = (XL - np.sqrt(RL*((RS-RL)*(RS-RL) + XL*XL)/RS))/(RL-RS)
        if (t2 < 0):
            dl2 = (np.pi + np.arctan(t2)) / (2 * np.pi)
        else:
            dl2 = (np.arctan(t2)) / (2 * np.pi)
        B2 = (RL * RL * t2 - (RS - XL * t2) * (RS * t2 + XL)) / (RS * (RL * RL + (RS * t2 + XL) * (RS * t2 + XL)));

        if (t1 != 0):
            d = dl1 * lambda_
            if (StubType == 2):
                ll = -(np.arctan(B1 * RS)) / (2 * np.pi)
            else:
                ll = (np.arctan(1. / (1. * B1 * RS))) / (2 * np.pi);

            if ((StubType == 2) and (ll < 0)):
                ll = ll + 0.5
            if ((StubType == 1) and (ll > 0.5)):
                ll -= 0.5
        
            lstub = ll * lambda_
        else:
            if (t2 != 0):
                d = dl2 * lambda_
                if (StubType == 2):
                    ll = -(np.arctan(B2 * RS)) / (2 * np.pi)
                else:
                    ll = (np.arctan(1. / (1. * B2 * RS))) / (2 * np.pi)
            
            if ((StubType == 2) and (ll < 0)):
                ll += 0.5
            if ((StubType == 1) and (ll > 0.5)):
                ll -= 0.5
            lstub = ll * lambda_

    # Convert d and lstub to degrees
    d = 360*f0*d/299792458
    lstub = 360*f0*lstub/299792458

    return d, lstub


def SingleStub_MatchingNetwork(params):

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
       
    [dline, lstub] = synthesize_SingleStub_Matching_Network(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'SingleStub' + str(int(StubType))
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

    # Stub
    # Drawing
    d += TransmissionLine().down().label("l = " + str(round(lstub, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').linewidth(1)
    if (StubType == 1): # Short
        comp_val['SC_Z0'] = RS
        comp_val['SC_ang'] = lstub

        d += elm.Ground().linewidth(1)
    else:
        comp_val['OC_Z0'] = RS
        comp_val['OC_ang'] = lstub
    
    d.pop()

    d += elm.Line().right().length(1).linewidth(1)

    # Line
    # Drawing
    d += TransmissionLine().right().label("l = " + str(round(dline, 1)) + " deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    comp_val['TL_Z0'] = RS
    comp_val['TL_ang'] = dline

    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val