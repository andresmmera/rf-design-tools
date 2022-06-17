# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
#from mysql.connector import connection
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *
from ..components import TransmissionLine

def synthesize_DC_Filter_C_Coupled_Shunt_Resonators(params):
    Lr = params['Xres']
    gi = params['gi']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']

    GA = 1/RS
    GB = 1/RL

    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0
    # Array of components
    Cseries = []
    J = []
    
    # Resonator capacitance as specified by the user. Later, the capacitance from the pi-C inverters will be substracted
    Cr = []
    Lres = []
    for i in range(0, N):
        Lres.append(float(Lr[i])) # It must be float
        Cr.append(1 / (Lres[i] * w0*w0) ) # [1] Fig. 8.11-1 (1)
    
    # Calculation of the coupling coefficients
    J.append(np.sqrt( (GA * w0 * Cr[0] * w) / (gi[0]*gi[1]) )) # J01 - First series coupling capacitor. [1] Fig. 8.11-1 (2)
    
    for i in range(1, N): # Intermediate coupling capacitors
        J.append((w*w0) * np.sqrt((Cr[i-1]*Cr[i]) / (gi[i]*gi[i+1]))) # [1] Fig. 8.11-1 (3)
        
    J.append(np.sqrt((GB * w0 * Cr[-1] * w) / (gi[-2] * gi[-1]))) # Jn, n+1 - Last series coupling capacitor. [1] Fig. 8.11-1 (4)
    
    # Calculation of the coupling capacitances
    Cseries.append( J[0] / (w0 * np.sqrt(1 - np.power(J[0] / GA, 2))) ) #C01. [1] Fig. 8.11-1 (5)
                  
    for i in range(1, N):
        Cseries.append(J[i] / w0) # Ci, i+1. [1] Fig. 8.11-1 (6)

    Cseries.append(J[-1] / (w0 * np.sqrt(1 - np.power(J[-1] / GB, 2)))) # [1] Fig. 8.11-1 (7)
                  
    # Excess of capacitance of first and last resonator
    C01e = Cseries[0] / (1 + np.power(w0*Cseries[0]/GA, 2)) # First resonator. [1] Fig. 8.11-1 (11)
    Cn_np1e = Cseries[-1] / (1 + np.power(w0*Cseries[-1]/GB, 2)) # Last resonator. [1] Fig. 8.11-1 (12)
    
    # Net shunt capacitances
    Cres = []
    Cres.append(Cr[0] - C01e - Cseries[1]) # [1] Fig. 8.11-1 (8)
    
    for i in range(1, N-1):
        Cres.append(Cr[i] - Cseries[i] - Cseries[i+1]) # [1] Fig. 8.11-1 (9)
        
    Cres.append(Cr[-1] - Cseries[-2] - Cn_np1e) # [1] Fig. 8.11-1 (10)

    return Cseries, Lres, Cres



# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 482
def DirectCoupled_C_Coupled_ShuntResonators(gi, RS, RL, f0, BW, Lres, fstart, fstop, npoints):
    Nres = len(gi) - 2 # Number of resonators
    bw = BW / f0
    
    # Calculation of w1, w2, w - 8.11-1 (15)
    f1 = f0 - BW / 2
    f2 = f0 + BW / 2
    
    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0
    
    # Calculation of GA and GB
    GA = 1 / RS
    GB = 1 / RL
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    # Component counter
    count_C = 0
    count_L = 0
    count_gnd = 0
    
    params = {}
    params['Xres'] = Lres
    params['gi'] = gi
    params['N'] = Nres
    params['ZS'] = RS
    params['ZL'] = RL
    params['f1'] = f1
    params['f2'] = f2
    Cseries, Lres, Cres = synthesize_DC_Filter_C_Coupled_Shunt_Resonators(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Direct-Coupled'
    NetworkType['DC_Type'] = 'C-Coupled Shunt Resonators'    
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['N'] = Nres
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
 
    
    # First coupling capacitor
    # Drawing
    d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[0], 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_C += 1
    comp_val['C'+str(count_C)] = Cseries[0]
        
    for i in range (0, Nres):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Line().down().length(1).linewidth(1)
        d.push()
        d += elm.Line().left().length(1.5).linewidth(1)
        d += elm.Capacitor().down().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)

        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lres[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)
        
        # Network
        count_C += 1      
        count_L += 1

        comp_val['C'+str(count_C)] = Cres[i]
        comp_val['L'+str(count_L)] = Lres[i]
        
        # Next coupling capacitor
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[i+1], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1.5).linewidth(1)
        
        # Network
        count_C += 1
        comp_val['C'+str(count_C)] = Cseries[i+1]
        
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

       
    return d, NetworkType, comp_val

def synthesize_DC_Filter_L_Coupled_Shunt_Resonators(params):
    
    Cres = params['Xres']
    gi = params['gi']
    Nres =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']
   
    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0
    
    # Calculation of GA and GB
    GA = 1 / RS
    GB = 1 / RL

    # Array of components
    Lseries = []
    J = []
    
    # Resonator capacitance as specified by the user. Later, the capacitance from the pi-C inverters will be substracted
    Lr = []
    Cres = [float(i) for i in params['Xres']]
    for i in range(0, Nres):
        Lr.append(1 / (Cres[i] * w0*w0) ) # [1] Fig. 8.11-1 (1)
    
    # Calculation of the coupling coefficients
    J.append(np.sqrt( (GA * w0 * Cres[0] * w) / (gi[0]*gi[1]) )) # J01 - First series coupling capacitor. [1] Fig. 8.11-1 (2)
    
    for i in range(1, Nres): # Intermediate coupling capacitors
        J.append((w*w0) * np.sqrt((Cres[i-1]*Cres[i]) / (gi[i]*gi[i+1]))) # [1] Fig. 8.11-1 (3)
        
    J.append(np.sqrt((GB * w0 * Cres[-1] * w) / (gi[-2] * gi[-1]))) # Jn, n+1 - Last series coupling capacitor. [1] Fig. 8.11-1 (4)
    
    # Calculation of the coupling capacitances
    Lseries.append( np.sqrt(1 - np.power(J[0] / GA, 2)) / (w0 * J[0]) ) #L01. [1] Fig. 8.11-1 (5)
                  
    for i in range(1, Nres):
        Lseries.append( 1 / (J[i] * w0)) # Li, i+1. [1] Fig. 8.11-1 (6)

    Lseries.append(np.sqrt( (1 - np.power(J[-1] / GB, 2))) / (w0 * J[-1])) # [1] Fig. 8.11-1 (7)
                  
    # Excess of capacitance of first and last resonator
    L01e = Lseries[0] * (1 + np.power(1/(GA * w0 * Lseries[0]), 2)) # First resonator. [1] Fig. 8.11-1 (11)
    Ln_np1e = Lseries[-1] * (1 + np.power(1/(GB * w0 * Lseries[-1]), 2)) # Last resonator. [1] Fig. 8.11-1 (12)
    
    # Net shunt capacitances
    Lres = []
    Lres.append( 1/(1/Lr[0] - 1/L01e - 1/Lseries[1]))  # [1] Fig. 8.11-1 (8)
    
    for i in range(1, Nres-1):
        Lres.append(1 / (1/Lr[i] - 1/Lseries[i] - 1/Lseries[i+1])) # [1] Fig. 8.11-1 (9)
        
    Lres.append(1 / (1/Lr[-1] - 1/Lseries[-2] - 1/Ln_np1e)) # [1] Fig. 8.11-1 (10)

    return Lseries, Lres, Cres

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 482
def DirectCoupled_L_Coupled_ShuntResonators(gi, RS, RL, f0, BW, Cres, fstart, fstop, npoints):
    Nres = len(gi) - 2 # Number of resonators
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    
    # Component counter
    count_C = 0
    count_L = 0

    params = {}
    params['Xres'] = Cres
    params['gi'] = gi
    params['N'] = Nres
    params['ZS'] = RS
    params['ZL'] = RL
    params['f1'] = f0-BW/2
    params['f2'] = f0+BW/2
    Lseries, Lres, Cres = synthesize_DC_Filter_L_Coupled_Shunt_Resonators(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Direct-Coupled'
    NetworkType['DC_Type'] = 'L-Coupled Shunt Resonators'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['N'] = Nres
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
        
    # First coupling inductor
    # Drawing
    d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[0], 'Inductance'), fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_L += 1
    comp_val['L'+str(count_L)] = Lseries[0]
    
    
    for i in range (0, Nres):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Line().down().length(1).linewidth(1)
        d.push()
        d += elm.Line().left().length(1.5).linewidth(1)
        d += elm.Capacitor().down().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)

        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lres[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)
        
        # Network
        count_C += 1
        count_L += 1
    
        comp_val['L'+str(count_L)] = Lres[i]
        comp_val['C'+str(count_C)] = Cres[i]
        
        # Next coupling inductor
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[i+1], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1.5).linewidth(1)
        
        # Network
        count_L += 1
        comp_val['L'+str(count_L)] = Lseries[i+1]
                
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val


def synthesize_DC_Filter_L_Coupled_Series_Resonators(params):

    f1 = params['f1']
    f2 = params['f2']
    Nres = params['N']
    Cres = params['Xres']
    RS = params['ZS']
    RL = params['ZL']
    gi = params['gi']
    Magnetic_Coupling = params['Magnetic_Coupling']

    Nres = len(gi) - 2 # Number of resonators

    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0

    # Array of components
    K = []
    
    # Resonator capacitance as specified by the user. Later, the capacitance from the pi-C inverters will be substracted
    Lres = []
    Cr = []
    for i in range(0, Nres): # The resonator inductances are the indexes 1 to (Nres + 1). L0 and Ln+1 are the port couplings
        Cr.append(float(Cres[i]))
        Lres.append(1 / (Cr[i] * w0*w0) ) # [1] Fig. 8.11-2 (1)
    Lres = np.insert(Lres, 0, Lres[0], axis=0)
    Lres = np.append(Lres, Lres[-1])
    Cres = Cr
    
    # Calculation of the shunt couplings
    K.append(np.sqrt( (RS * w0 * Lres[1] * w) / (gi[0]*gi[1]) )) # K01 - First shunt coupling. [1] Fig. 8.11-2 (2)
    
    for i in range(1, Nres): # Intermediate mutual coupling coefficients
        K.append((w*w0) * np.sqrt((Lres[i]*Lres[i+1]) / (gi[i]*gi[i+1]))) # [1] Fig. 8.11-2 (3)
        
    K.append(np.sqrt((RL * w0 * Lres[-2] * w) / (gi[-2] * gi[-1]))) # Kn, n+1 - Last shunt coupling. [1] Fig. 8.11-2 (4)
    
    # Calculation of the shunt couplings
    M = []
    M.append( (K[0]/w0) * np.sqrt(1 + np.power((w0*Lres[0])/RS, 2))) #M01. [1] Fig. 8.11-2 (5)
                  
    for i in range(1, Nres):
        M.append(K[i] / w0) # Mi, i+1. [1] Fig. 8.11-2 (6)

    M.append((K[-1]/w0) * np.sqrt(1 + np.power(w0 * Lres[-1]/RL, 2))) # [1] Fig. 8.11-1 (7)
                  
    
    
    # Excess of coupling inductance
    Me = []
    M01e = (M[0] + (((Lres[0] - M[0])*w0*w0*M[0]*Lres[0])/(RS*RS))) / (1 + np.power(w0*Lres[0]/RS, 2))# M01e. [1] Fig. 8.11-2 (13)
    Mn_np1e = (M[-1] + (((Lres[-1] - M[-1])*w0*w0*M[-1]*Lres[-1])/(RL*RL))) / (1 + np.power(w0*Lres[-1]/RL, 2))# Mn, n+1 e. [1] Fig. 8.11-2 (13)

    if (Magnetic_Coupling == 0):
        # The transformers are replaced by the equivalent circuit resulting in series resonators coupled with shunt inductors
        
        # Series inductances
        Lseries = []
        Lseries.append(Lres[0] - M[0]); # L0. [1] Fig. 8.11-2 (8)
        Lseries.append(Lres[1] - M01e - M[1]); # L1. [1] Fig. 8.11-2 (9)

        for i in range(2, Nres):
            Lseries.append(Lres[i] - M[i-1] - M[i])

        Lseries.append(Lres[-2] - M[-2] - Mn_np1e);
        Lseries.append(Lres[-1] - M[-1])

        return M, Lseries, Cres
        
    else:
        # Transformer inductance
        Lp = []
        Lp.append(Lres[0]) # Lp0. [1] Fig. 8.11-2 (15)
        Lp.append(Lres[1] + M[0] - M01e) # Lp0. [1] Fig. 8.11-2 (16)
        
        for i in range(2, Nres):
            Lp.append(Lres[i]) # Lpj. [1] Fig. 8.11-2 (17)
        Lp.append(Lres[-2] + M[-1] - Mn_np1e) # Lpn. [1] Fig. 8.11-2 (18)
        Lp.append(Lres[-1]) # Lpn+1. [1] Fig. 8.11-2 (19)
        
        # Halve resonator inductances
        for i in range (1, Nres+1):
            Lp[i] = Lp[i]/2

        return M, Lp, Cres


# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 484
def DirectCoupled_L_Coupled_SeriesResonators(params):
    gi = params['gi']
    RS = params['ZS']
    RL = params['ZL']
    f1 = params['f1']
    f2 = params['f2']
    f0 = params['fc']
    Magnetic_Coupling = params['Magnetic_Coupling']
    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']

    w0 = 2*np.pi*f0*1e6

    Nres = len(gi) - 2 # Number of resonators 
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
   
    # Component counter
    count_C = 0
    count_L = 0
    
    params['f1'] = params['f1'] *1e6
    params['f2'] = params['f2'] *1e6
    M, Lseries, Cres = synthesize_DC_Filter_L_Coupled_Series_Resonators(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Direct-Coupled'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['N'] = Nres
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL
    
              
    if (Magnetic_Coupling == 0):
        NetworkType['DC_Type'] = 'L-Coupled Series Resonators'      
        # Source port
        # Drawing: Source port and the first line
        d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line().length(1).linewidth(1)

        # First coupling inductor
        # Drawing
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[0], 'Inductance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_L += 1
        comp_val['L'+str(count_L)] = Lseries[0]

        for i in range (0, Nres+1):
            d.push()
            # Coupling
            # Drawing
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(M[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)

            #Network
            count_L += 1
            comp_val['L'+str(count_L)] = M[i]

            d.pop()
            # Series resonator
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[i+1], 'Inductance'), fontsize=_fontsize).linewidth(1)        
            count_L += 1
            comp_val['L'+str(count_L)] = Lseries[i+1]

            if (i < Nres):
                d += elm.Capacitor().right().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
                count_C += 1
                comp_val['C'+str(count_C)] = Cres[i]
           

        # Drawing
        d += elm.Line().length(1).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)

    else:
        # Magnetic coupling
        NetworkType['DC_Type'] = 'Magnetic coupled resonators'
        Lp = Lseries
                       
        # Source port
        # Drawing: Source port and the first line
        d += elm.Line(color='white').length(2).linewidth(0)
        d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line().length(2).linewidth(1)
               
        count_L = 0
        count_C = 0
        count_gnd = 0
               
        for i in range (0, Nres):
            x = d.add(elm.Transformer(t1=4, t2=4, loop=True, core = True, fontsize=_fontsize)
                      .label(getUnitsWithScale(Lp[i], 'Inductance'), loc='left')
                      .label(getUnitsWithScale(Lp[i+1], 'Inductance'), loc='right')
                      .label("k = " + str(round(M[i]/np.sqrt(Lp[i]*Lp[i+1]), 3)), loc='top')
                      .flip())
            d += elm.Ground().at(x.p1).linewidth(1)
            d += elm.Ground().at(x.s1).linewidth(1)
            d += elm.Line().at(x.s2).length(1) 
            d += elm.Capacitor().right().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().length(1)
            
            # Network: The transformer is simulated using the uncoupled lumped equivalen (Zverev, Fig. 10.4 (c))
            count_L += 1
            comp_val['L'+str(count_L)] = Lp[i] - M[i]

            count_L += 1
            comp_val['L'+str(count_L)] = M[i]

            count_L += 1
            comp_val['L'+str(count_L)] = Lp[i+1] - M[i]

            count_gnd += 1
            count_C += 1
            comp_val['C'+str(count_C)] = Cres[i]
            
            print("L[" + str(3*i) + "] = ", getUnitsWithScale(Lp[i] - M[i], 'Inductance'))
            print("L[" + str(3*i+1) + "] = ", getUnitsWithScale(M[i], 'Inductance'))
            print("L[" + str(3*i+2) + "] = ", getUnitsWithScale(Lp[i+1] - M[i], 'Inductance'))
            print("C[" + str(i) + "] = ", getUnitsWithScale(Cres[i], 'Capacitance'))
            
        x = d.add(elm.Transformer(t1=4, t2=4, loop = True, core = True, fontsize=_fontsize)
                      .label(getUnitsWithScale(Lp[-2], 'Inductance'), loc='left')
                      .label(getUnitsWithScale(Lp[-1], 'Inductance'), loc='right')
                      .label("k = " + str(round(M[-1]/np.sqrt(Lp[-2]*Lp[-1]), 3)), loc='top')
                      .flip())
        d += elm.Ground().at(x.p1).linewidth(1)
        d += elm.Ground().at(x.s1).linewidth(1)
        
        # Network: The transformer is simulated using the uncoupled lumped equivalen (Zverev, Fig. 10.4 (c))
        count_L += 1
        comp_val['L'+str(count_L)] = Lp[-2] - M[-1]

        count_L += 1
        comp_val['L'+str(count_L)] = M[-1]

        count_L += 1
        comp_val['L'+str(count_L)] = Lp[-1] - M[-1]
        
        count_gnd += 1
                       
        # Load port
        d += elm.Line().at(x.s2).length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(RL) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
            
    return d, NetworkType, comp_val


def synthesize_DC_Filter_C_Coupled_Series_Resonators(params):

    f1 = params['f1']
    f2 = params['f2']
    Nres = params['N']
    Lres = params['Xres']
    RS = params['ZS']
    RL = params['ZL']
    gi = params['gi']
    port_match = ['C', 'C']

    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0

        # Array of components
    K = []
    
    # Resonator capacitance as specified by the user. Later, the capacitance from the pi-C inverters will be substracted
    Cres = []
    for i in range(0, Nres):
        Cres.append(1 / (Lres[i] * w0*w0) ) # [1] Fig. 8.11-1 (1)
    
    # Calculation of the coupling coefficients
    K.append(np.sqrt( (RS * w0 * Lres[0] * w) / (gi[0]*gi[1]) )) # K01 - First shunt coupling. [1] Fig. 8.11-2 (2)
    
    for i in range(1, Nres): # Intermediate coupling coeffcuebts
        K.append((w*w0) * np.sqrt((Lres[i-1]*Lres[i]) / (gi[i]*gi[i+1]))) # [1] Fig. 8.11-2 (3)
        
    K.append(np.sqrt((RL * w0 * Lres[-1] * w) / (gi[-2] * gi[-1]))) # Kn, n+1 - Last shunt coupling. [1] Fig. 8.11-2 (4)
    
    # Calculation of the capacitive inverters # [2] Fig. 10.83 b)
    Cinv = []
    for i in range(0, Nres+1):
        Cinv.append(1/(w0*K[i]))
        
        
    # Absorb the negative capacitance of the upper branch of the inverter into the capacitance of the resonator (Cres)
    # The result is the series equivalent of the original Cres[i] with two inverter capacitances (one at each side of the resonator)
    for i in range(0, Nres):
        Cres[i] = 1/((-1/Cinv[i]) + (1/Cres[i]) + (-1/Cinv[i+1]))
        
    # Next, we need to convert the negative capacitance of the upper side of the inverter in the source and in the load port. For this, 
    # it is needed to apply the series to parallel transform and then step-up the port impedances with a reactance, preferably a capacitor
    # because of their higher Q and to reduce the number of tuning elements, but it may also be an inductor depending on the needs (e.g. if you need
    # to make a diplexer and mix with a highpass filter)
    
    # 1. Source port
    
    # Series to parallel conversion
    Xseries = -1/(w0*Cinv[0]) # Reactance of the upper branch of the inverter (negative)
    Rp = (RS*RS + Xseries*Xseries) / RS
    Xp = (RS*RS + Xseries*Xseries) / Xseries
    
    C0 = 1/(w0*Xp) # Capacitance of the shunt counterpart (negative)
    
    Cinv[0] += C0 # Absorb the negative capacitance into the first shunt capacitor
    
    # Now Rp != RS, then as said, it is needed to compensate such difference with a reactance
    if (port_match[0] == 'C'):
        Cmatch_source = 1/(w0 * (Rp - RS))
    else:
        Lmatch_source = (Rp - RS)/w0
    
    # 2. Load port
    
    # Series to parallel conversion
    Xseries = -1/(w0*Cinv[-1]) # Reactance of the upper branch of the inverter (negative)
    Rp = (RL*RL + Xseries*Xseries) / RL
    Xp = (RL*RL + Xseries*Xseries) / Xseries
    
    Clast = 1/(w0*Xp) # Capacitance of the shunt counterpart (negative)
    
    Cinv[-1] += Clast # Absorb the negative capacitance into the last shunt capacitor
    
    # Now Rp != RL, then as said, it is needed to compensate such difference with a reactance
    if (port_match[1] == 'C'):
        Cmatch_load = 1/(w0 * (Rp - RL))
    else:
        Lmatch_load = (Rp - RL)/w0

    return Cmatch_source, Cmatch_load, Cinv, Lres, Cres

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# References:
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 484
# [2] "Filter Handbook", Anatol I. Zverev. John Wiley and Sons, 1967, pages 562-563

def DirectCoupled_C_Coupled_SeriesResonators(params, port_match):
    gi = params['gi']
    f1 = params['f1']
    f2 = params['f2']
    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']
    RS = params['ZS']
    RL = params['ZL']

    Nres = len(gi) - 2 # Number of resonators
    
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
    count_L = 0
    count_gnd = 0
    
    syn_params = {}
    syn_params['gi'] = params['gi']
    syn_params['N'] = params['N']
    syn_params['ZS'] = params['ZS']
    syn_params['ZL'] = params['ZL']
    syn_params['f1'] = float(params['f1'])*1e6
    syn_params['f2'] = float(params['f2'])*1e6
    syn_params['Xres'] = [float(i)*1e-9 for i in params['Xres']] # Resonator inductance
    Match_source, Match_load, Cinv, Lres, Cres = synthesize_DC_Filter_C_Coupled_Series_Resonators(syn_params)
    
    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Direct-Coupled'
    NetworkType['DC_Type'] = 'C-Coupled Series Resonators'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['N'] = Nres
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL

    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize, loc='bottom').linewidth(1)
    d += elm.Line().length(1).linewidth(1)
       
    # First coupling
    
    if (port_match[0] == 'C'):
        # Drawing
        d += elm.Capacitor().right().label(getUnitsWithScale(Match_source, 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)

        # Network
        count_C += 1
        comp_val['C'+str(count_C)] = Match_source
    
    else:
        # Drawing
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Match_source, 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)

        comp_val['L'+str(count_L)] = Match_source

    
    for i in range (0, Nres):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Capacitor().down().label(getUnitsWithScale(Cinv[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)
        
        # Network
        count_C += 1
        comp_val['C'+str(count_C)] = Cinv[i]
        
        d.pop()
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lres[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Capacitor().right().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        
        count_L += 1
        count_C += 1

        comp_val['L'+str(count_L)] = Lres[i]
        comp_val['C'+str(count_C)] = Cres[i]
        
    # Drawing
    d.push()
    d += elm.Capacitor().down().label(getUnitsWithScale(Cinv[-1], 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)

    count_C += 1
    comp_val['C'+str(count_C)] = Cinv[-1]
    
    d.pop()
    if (port_match[1] == 'C'):
        d += elm.Capacitor().right().label(getUnitsWithScale(Match_load, 'Capacitance'), fontsize=_fontsize).linewidth(1)
        count_C += 1
        comp_val['C'+str(count_C)] = Match_load
        
    else:
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Match_load, 'Inductance'), fontsize=_fontsize).linewidth(1)
        count_L += 1
        comp_val['L'+str(count_L)] = Match_load
    
    # Load port
    # Drawing
    d += elm.Line().length(1).linewidth(1)
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize, loc='bottom').linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d, NetworkType, comp_val


def synthesize_DC_Filter_QW_Shunt_Resonators(params):

    f1 = params['f1']
    f2 = params['f2']
    RS = params['ZS']
    gi = params['gi']
    Nres = params['N']
    
    w1 = 2*np.pi*f1
    w2 = 2*np.pi*f2
    f0 = (f1+f2)/2
    
    w0 = np.sqrt(w1*w2)
    w = (w2 - w1) / w0
    
    # Calculation of GA and GB
    Y0 = 1/RS

    # Bi/Y0
    by = []
    Cres = []
    Lres = []
    by.append(gi[0]*gi[1]/w - np.pi/4) # [1] b1/Y0 Fig. 8.10-1 (1)
    Cres.append(by[0]*Y0/w0)
    Lres.append(1/(w0*w0*Cres[0]))
    
    for i in range(1, Nres-1):
        if (i % 2 == 1): # Even 
            by.append(gi[i+1]/(w * gi[0]) - np.pi/2) # [1] Fig. 8.10-1 (3)
        else: # Odd
            by.append(gi[i+1] * gi[0]/w  - np.pi/2) # [1] Fig. 8.10-1 (2)
            
        Cres.append(by[i]*Y0/w0)
        Lres.append(1/(w0*w0*Cres[i]))
    by.append(by[0]) # [1] Fig. 8.10-1 (4)
    Cres.append(Cres[0])
    Lres.append(Lres[0])
    
    C0 = 299792458 # m/s
    wavelength = C0/f0
    qw = wavelength / 4 # lambda / 4
    RL = RS/gi[-1]

    return RS, RL, qw, Lres, Cres

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 482
def DirectCoupled_QW_Coupled_ShuntResonators(gi, RS, RL, f0, BW, fstart, fstop, npoints):
    Nres = len(gi) - 2 # Number of resonators   

    params = {}
    params['gi'] = gi
    params['N'] = Nres
    params['ZS'] = RS
    params['ZL'] = RL
    params['f1'] = f0-BW/2
    params['f2'] = f0+BW/2
    RS, RL, qw, Lres, Cres = synthesize_DC_Filter_QW_Shunt_Resonators(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['Network'] = 'Direct-Coupled'
    NetworkType['DC_Type'] = 'Quarter-Wave coupled resonators'
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['N'] = Nres
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing()
    _fontsize = 12
    
    # Component counter
    count_C = 0
    count_L = 0
    count_TL = 0
    
    # Source port
    # Drawing: Source port and the first line
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    d += elm.Line().right().length(1).linewidth(1)
        
    for i in range (0, Nres):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Line().down().length(1).linewidth(1)
        d.push()
        d += elm.Line().left().length(1).linewidth(1)
        d += elm.Capacitor().down().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)

        d.pop()
        d += elm.Line().right().length(1).linewidth(1)
        d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lres[i], 'Inductance'), fontsize=_fontsize, loc='bottom').linewidth(1)
        d += elm.Ground().linewidth(1)
        
        # Network
        count_C += 1       
        count_L += 1

        comp_val['C'+str(count_C)] = Cres[i]
        comp_val['L'+str(count_L)] = Lres[i]
        
        # Coupling line
        # Drawing
        d.pop()
        d += elm.Line().right().length(2).linewidth(1)
        d += TransmissionLine().right().label("l = " + getUnitsWithScale(qw, 'Distance'), fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top').linewidth(1)
        d += elm.Line().right().length(2).linewidth(1)
        
        count_TL += 1
        comp_val['TL_'+str(count_TL)+'_Z0'] = RS;
        comp_val['TL_'+str(count_TL)+'_ang'] = 90;
       
        
    # Load port
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    # Network
    comp_val['ZL'] = RL

       
    return d, NetworkType, comp_val