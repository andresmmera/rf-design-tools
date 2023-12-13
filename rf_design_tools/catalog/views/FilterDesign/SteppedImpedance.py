# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
#from mysql.connector import connection
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *
from ..components import TransmissionLine

# Reference: Microwave Engineering. David M. Pozar. 4th Edition. 2012. John Wiley and Sons. Page 424.
def synthesize_SteppedImpedance(params):

    gi = params['gi']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']
    FirstElement = params['FirstElement']

    Zlow = params['Zlow']
    Zhigh = params['Zhigh']


    beta = 2 * np.pi * fc / 299792458;


    Z = []
    l = []

    for i in range(0, N):
        if (((FirstElement != 1) and (i % 2 == 0)) or ((FirstElement == 1) and (i % 2 != 0))):
            # Shunt capacitor
            Z.append(Zlow)
            l.append(gi[i + 1] * Zlow / (beta * RS))
        else:
            Z.append(Zhigh)
            l.append(gi[i + 1] * RS / (beta * Zhigh))
    
    if (((FirstElement != 1) and (i % 2 == 0)) or ((FirstElement == 1) and (i % 2 != 0))):
        RL = RL * gi[N + 1]
    else:
        RL = RL / gi[N + 1]
  
    return Z, l, RL



def SteppedImpedance_Filter(params):

    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']

    N = params['N']

    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']
    
    
       
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    # Component counter
    count_TL = 0

    

    [Z, l, RL] = synthesize_SteppedImpedance(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Stepped Impedance'
    NetworkType['Mask'] = 'LPF'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['f0'] = fc
    NetworkType['N'] = N
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL

    c0 = 299792458
    lambda_ = c0 / fc

        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
 
     
    for i in range (0, N):
        # Resonator
        
        # Drawing
        d += TransmissionLine().right().label("l = " + str(round((180*np.pi)*l[i]/lambda_,2)) + " deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + getUnitsWithScale(Z[i], 'Impedance'), loc = 'top', fontsize=_fontsize).linewidth(1)

        d += elm.Line().right().length(1).linewidth(1)
        
        # Network
        count_TL += 1
        comp_val['TL_'+str(count_TL)+'_Z0'] = Z[i];
        comp_val['TL_'+str(count_TL)+'_ang'] = l[i];
  
        
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

       
    return d, NetworkType, comp_val
