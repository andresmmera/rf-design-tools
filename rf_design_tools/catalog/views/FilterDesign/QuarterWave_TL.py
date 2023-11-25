# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
#from mysql.connector import connection
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *
from ..components import TransmissionLine

# Reference: 
# [1] "Microwave Engineering", David M. Pozar, Wiley 2012. Eq. 8.131
def synthesize_QW(params):

    gi = params['gi']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']
    fc = params['fc']
    BW = f2-f1
    bw = BW / fc # Fractional BW

    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    delta = (w2 - w1) / w0
    # Array of Z0s
    Z = []

    if (params['Mask']== 'Bandpass'):
        # BPF
        for i in range(0, N):
            Z.append((np.pi*RS)/(np.pi*gi[i]*delta))
    else:
        # BSF
        for i in range(0, N):
            Z.append((4*RS)/(np.pi*gi[i]*delta))

    return Z



def QW_TransmissionLine_Filter(params):

    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']
    f0 = 0.5*(f2+f1)
    N = params['N']
    BW = f2-f1
    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']
    
    
    bw = BW / f0
    
    # Calculation of w1, w2, w - 8.11-1 (15)
    f1 = f0 - BW / 2
    f2 = f0 + BW / 2
    
    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0
    
    lambda4 = 299792458 / (4. * f0)
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    # Component counter
    count_TL = 0
    count_TL_OC = 0
    count_TL_SC = 0
    count_gnd = 0
    

    Z = synthesize_QW(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Quarter-Wave TL'
    NetworkType['Mask'] = 'BPF'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['f0'] = w0/(2*np.pi)
    NetworkType['N'] = N
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL

    if (params['Mask']== 'Bandstop'):
        NetworkType['Mask'] = 'BSF'
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
 
    
    # First coupling TL
    # Drawing
    d += TransmissionLine().right().label("l = 90 deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_TL += 1
    comp_val['TL_'+str(count_TL)+'_Z0'] = RS;
    comp_val['TL_'+str(count_TL)+'_ang'] = 90;
  
    for i in range (0, N):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Line().down().length(1).linewidth(1)
        d += TransmissionLine().down().label("Z\u2080 = " + getUnitsWithScale(Z[i], 'Impedance')+"\nl = 90 deg", fontsize=_fontsize, loc = 'bottom').linewidth(1)

        if (params['Mask']== 'Bandstop'):
            # BSF
            d += elm.Ground().linewidth(1)
            count_gnd += 1

            # Network
            count_TL_SC += 1
            comp_val['TL_SC_'+str(count_TL_SC)+'_Z0'] = Z[i];
            comp_val['TL_SC_'+str(count_TL_SC)+'_ang'] = 90;
        else:
            # Network
            count_TL_OC += 1
            comp_val['TL_OC_'+str(count_TL_OC)+'_Z0'] = Z[i];
            comp_val['TL_OC_'+str(count_TL_OC)+'_ang'] = 90;

        
        # Next coupling line
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += TransmissionLine().right().label("l = 90 deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)
        
        # Network
        count_TL += 1
        comp_val['TL_'+str(count_TL)+'_Z0'] = RS;
        comp_val['TL_'+str(count_TL)+'_ang'] = 90;
        
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

       
    return d, NetworkType, comp_val
