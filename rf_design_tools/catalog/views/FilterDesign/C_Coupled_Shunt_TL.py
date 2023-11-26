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
def synthesize_C_Coupled_Shunt_TL(params):

    gi = params['gi']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']

    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    w0 = np.sqrt(w1*w2)
    f0 = w0/(2*np.pi)

    delta = (w2 - w1) / w0

    lambda0 = 2*np.pi*299792458/w0

    J = []
    C = []
    deltaC = []
    l = []

    for i in range(0, N):
        if (i == 0):
            J.append(np.sqrt(np.pi * delta / (4 * gi[i + 1])) / RS)
            C.append(J[i] / (w0 * np.sqrt(1 - RS * RS * J[i] * J[i])))
            continue

        
        J.append((0.25 * np.pi * delta / np.sqrt(gi[i+1] * gi[i])) / RS);
        C.append(J[i] / w0);
        deltaC.append( -C[i - 1] - C[i]);
        l.append(lambda0 / 4 + (RS * w0 * deltaC[i - 1] / (2 * np.pi)) * lambda0);
    
        if (l[i - 1] < 0):
            l[i - 1] += lambda0 / 4;
    
    # Last short stub + C series section
    J.append(np.sqrt(np.pi * delta / (4 * gi[N+1] * gi[N])) / RS);
    C.append(J[N] / (w0 * np.sqrt(1 - RS * RS * J[N] * J[N])));
    deltaC.append(-C[N] - C[N - 1]);
    l.append(lambda0 / 4 + (RS * w0 * deltaC[N - 1] / (2 * np.pi)) * lambda0);
    if (l[N - 1] < 0):
        l[N - 1] += lambda0 / 4;
    
    # Convert physical length to electrical length in deg
    for i in range(0, N):
        l[i] *= (180/np.pi)*(2*np.pi*f0/299792458)
  
    return C, l



def C_Coupled_ShuntResonators_TL_Filter(params):

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
        
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    # Component counter
    count_C = 0
    count_TL_SC = 0
    count_gnd = 0
    

    [C, E] = synthesize_C_Coupled_Shunt_TL(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'C-coupled shunt resonators (TL)'
    NetworkType['Mask'] = 'BPF'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['f0'] = w0/(2*np.pi)
    NetworkType['N'] = N
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL

        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
 
    
    # First coupling capacitor
    # Drawing
    d += elm.Capacitor().right().label(getUnitsWithScale(C[0], 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_C += 1
    comp_val['C'+str(count_C)] = C[0]
  
    for i in range (0, N):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Line().down().length(1).linewidth(1)
        d += TransmissionLine().down().label("Z\u2080 = " + getUnitsWithScale(RS, 'Impedance')+"\nl = " + str(round(E[i], 2)) + " deg", fontsize=_fontsize, loc = 'bottom').linewidth(1)
        d += elm.Ground().linewidth(1)

        # Network
        count_gnd += 1
        count_TL_SC += 1
        comp_val['TL_SC_'+str(count_TL_SC)+'_Z0'] = RS;
        comp_val['TL_SC_'+str(count_TL_SC)+'_ang'] = E[i];
  

        
        # Next coupling cap
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Capacitor().right().label(getUnitsWithScale(C[i+1], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)
        
        # Network
        count_C += 1
        comp_val['C'+str(count_C)] = C[i+1]
        
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

       
    return d, NetworkType, comp_val
