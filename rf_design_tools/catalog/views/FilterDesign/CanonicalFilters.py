# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# Import for the generation of the Qucs schematic
from datetime import date


def getCanonicalFilterNetwork(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
    ZL = params['ZL']
    fc = params['fc']
    f1 = params['f1']
    f2 = params['f2']
    FirstElement = params['FirstElement']
    Mask = params['Mask']
    f_start = params['f_start']
    f_stop = params['f_stop']
    n_points = params['n_points']
    Response = params['Response']
    Ripple = params['Ripple']

    if (Mask =='Bandpass' or Mask =='Bandstop'):
        w1 = 2*np.pi*f1*1e6 # rad/s
        w2 = 2*np.pi*f2*1e6 # rad/s
        w0 = np.sqrt(w1*w2)
        Delta = w2-w1
    else:
        w0 = 2*np.pi*fc*1e6 # rad/s

    count_C = 0
    count_L = 0
    count_gnd = 0
    
    C = []
    L = []
    ground = []

    comp_val = {} # Associative array for storing the value of the components
    comp_val['ZS'] = ZS
    

    NetworkType = {}
    NetworkType['Network'] = 'Canonical'
    NetworkType['Mask'] = Mask
    if FirstElement==1:  
        NetworkType['First_Element'] = 'Shunt'
        comp_val['ZL'] = ZS/gi[-1]
    else:
        NetworkType['First_Element'] = 'Series'
        comp_val['ZL'] = ZS*gi[-1]
    NetworkType['N'] = N
    NetworkType['freq'] = np.round_(np.linspace(f_start, f_stop, n_points))*1e6

    # Place components
    for i in range(0, N):
        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):           
            if (Mask == 'Lowpass'):
                # Shunt capacitance
                count_C += 1
                comp_val['C'+str(count_C)] = gi[i+1]/(ZS*w0)
            elif (Mask == 'Highpass'):
                # Shunt inductance
                count_L += 1
                comp_val['L'+str(count_L)] = ZS/(w0*gi[i+1])
            elif (Mask == 'Bandpass'):
                # Shunt parallel resonator
                count_C += 1
                count_L += 1
                comp_val['C'+str(count_C)] = gi[i+1]/(ZS*Delta)
                comp_val['L'+str(count_L)] = ZS*Delta/(gi[i+1]*w0*w0)
            elif (Mask == 'Bandstop'):
                # Shunt series resonator
                count_C += 1
                count_L += 1
                comp_val['C'+str(count_C)] = gi[i+1]*Delta/(ZS*w0*w0)
                comp_val['L'+str(count_L)] = ZS/(gi[i+1]*Delta)
           
        else:
            if (Mask == 'Lowpass'):
                # Series inductor
                count_L += 1
                comp_val['L'+str(count_L)] = ZS*gi[i+1]/w0
            elif (Mask == 'Highpass'):
                # Series capacitor
                count_C += 1
                comp_val['C'+str(count_C)] = 1/(gi[i+1]*w0*ZS)
            elif (Mask == 'Bandpass'):
                # Shunt parallel resonator
                count_C += 1
                count_L += 1
                comp_val['C'+str(count_C)] = Delta/(ZS*w0*w0*gi[i+1])
                comp_val['L'+str(count_L)] = ZS*gi[i+1]/(Delta)
            elif (Mask == 'Bandstop'):
                # Series parallel resonator
                count_C += 1
                count_L += 1
                comp_val['C'+str(count_C)] = 1/(ZS*Delta*gi[i+1])
                comp_val['L'+str(count_L)] = gi[i+1]*ZS*Delta/(w0*w0)
    
    return NetworkType, comp_val


def getCanonicalFilterSchematic(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
    fc = params['fc']
    f1 = params['f1']
    f2 = params['f2']
    FirstElement = params['FirstElement']
    Mask = params['Mask']

    if (Mask =='Bandpass' or Mask =='Bandstop'):
        w1 = 2*np.pi*f1*1e6 # rad/s
        w2 = 2*np.pi*f2*1e6 # rad/s
        w0 = np.sqrt(w1*w2)
        Delta = w2-w1
    else:
        w0 = 2*np.pi*fc*1e6 # rad/s

    print(gi)
    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(ZS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)
            
    # Draw the filter components
    for i in range(N):
        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):
            d += elm.Dot()
            d.push() # Save the drawing point for later
            
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(ZS*w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
            elif (Mask == 'Highpass'):
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS/(gi[i+1]*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
            elif (Mask == 'Bandpass'):
                d.push()
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Dot()
                d.push()
                d += elm.Line().left().length(1).linewidth(1)
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(ZS*Delta), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
                d += elm.Line().right().length(1).linewidth(1)
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS*Delta/(gi[i+1]*w0*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
            elif (Mask == 'Bandstop'):
                d += elm.Dot()
                d.push()
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS/(gi[i+1]*Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]*Delta/(ZS*w0*w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
                
            d.pop() # Restore the drawing point
        else:
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                d += elm.Inductor2(loops=2).label(getUnitsWithScale(ZS*gi[i+1]/w0, 'Inductance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Highpass'):
                d += elm.Capacitor().label(getUnitsWithScale(1/(gi[i+1]*w0*ZS), 'Capacitance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Bandpass'):
                d += elm.Inductor2(loops=2).label(getUnitsWithScale(ZS*gi[i+1]/(Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Capacitor().label(getUnitsWithScale(Delta/(ZS*w0*w0*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Bandstop'):
                d.push()
                d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(gi[i+1]*ZS*Delta/(w0*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d.pop()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Capacitor().right().label(getUnitsWithScale(1/(ZS*Delta*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)

    # Draw the last line (if needed) and the load port
    d += elm.Line().right().length(2).linewidth(1)
    if (FirstElement==1):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(ZS/gi[-1]))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(ZS*gi[-1]))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d