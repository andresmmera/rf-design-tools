# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm
from skrf.mathFunctions import find_closest

# Get units with scale, etc.
from ..utilities import *
from ..components import TransmissionLine

# standard imports
import skrf as rf
from skrf import network2

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
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
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
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    # Network: Port 1
    connections = [] # Network connections
    L = []
    C = []
    ground = []
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)
    
    # First coupling capacitor
    # Drawing
    d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[0], 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_C += 1
    C.append(line.capacitor(Cseries[0], name='C' + str(count_C)))
    
    connections.append([(Port1, 0), (C[0], 0)])
    
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
        C.append(line.capacitor(Cres[i], name='C' + str(count_C)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        count_L += 1
        L.append(line.inductor(Lres[i], name='L' + str(count_L)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        # Next coupling capacitor
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[i+1], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1.5).linewidth(1)
        
        # Network
        count_C += 1
        C.append(line.capacitor(Cseries[i+1], name='C' + str(count_C)))
        
        # Connections
        connections.append([(C[2*i], 1), (C[2*i+1], 0), (C[2*i+2], 0), (L[i], 0)])
        connections.append([(C[2*i+1], 1), (ground[2*i], 0)])
        connections.append([(L[i], 1), (ground[2*i+1], 0)])
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    # Network
    Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
    
    # Connections
    connections.append([(C[-1], 1), (Port2, 0)])
       
    return d, connections

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
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    # Component counter
    count_C = 0
    count_L = 0
    count_gnd = 0

    params = {}
    params['Xres'] = Cres
    params['gi'] = gi
    params['N'] = Nres
    params['ZS'] = RS
    params['ZL'] = RL
    params['f1'] = f0-BW/2
    params['f2'] = f0+BW/2
    Lseries, Lres, Cres = synthesize_DC_Filter_L_Coupled_Shunt_Resonators(params)
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    # Network: Port 1
    connections = [] # Network connections
    L = []
    C = []
    ground = []
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)
    
    # First coupling inductor
    # Drawing
    d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[0], 'Inductance'), fontsize=_fontsize).linewidth(1)
    d += elm.Line().right().length(1).linewidth(1)
    
    # Network
    count_L += 1
    L.append(line.inductor(Lseries[0], name='L' + str(count_L)))
    
    connections.append([(Port1, 0), (L[0], 0)])
    
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
        C.append(line.capacitor(Cres[i], name='C' + str(count_C)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        count_L += 1
        L.append(line.inductor(Lres[i], name='L' + str(count_L)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        # Next coupling inductor
        # Drawing
        d.pop()
        d += elm.Line().right().length(1.5).linewidth(1)
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[i+1], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1.5).linewidth(1)
        
        # Network
        count_L += 1
        L.append(line.inductor(Lseries[i+1], name='L' + str(count_L)))
        
        # Connections
        connections.append([(L[2*i], 1), (L[2*i+1], 0), (L[2*i+2], 0), (C[i], 0)])
        connections.append([(L[2*i+1], 1), (ground[2*i], 0)])
        connections.append([(C[i], 1), (ground[2*i+1], 0)])
        
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    # Network
    Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
    
    # Connections
    connections.append([(L[-1], 1), (Port2, 0)])
        
    return d, connections

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 484
def DirectCoupled_L_Coupled_SeriesResonators(gi, RS, RL, f0, BW, Lres, Magnetic_Coupling, fstart, fstop, npoints):
    Nres = len(gi) - 2 # Number of resonators
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
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    # Component counter
    count_C = 0
    count_L = 0
    count_gnd = 0
    
    # Array of components
    Cseries = []
    K = []
    
    # Resonator capacitance as specified by the user. Later, the capacitance from the pi-C inverters will be substracted
    Cseries = []
    for i in range(1, Nres+1): # The resonator inductances are the indexes 1 to (Nres + 1). L0 and Ln+1 are the port couplings
        Cseries.append(1 / (Lres[i] * w0*w0) ) # [1] Fig. 8.11-2 (1)
    
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
        
        # Source port
        # Drawing: Source port and the first line
        d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line().length(1).linewidth(1)

        # Network: Port 1
        connections = [] # Network connections
        L = []
        C = []
        ground = []
        Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)

        # First coupling inductor
        # Drawing
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[0], 'Inductance'), fontsize=_fontsize).linewidth(1)

        # Network
        count_L += 1
        L.append(line.inductor(Lseries[0], name='L' + str(count_L)))

        connections.append([(Port1, 0), (L[0], 0)])

        for i in range (0, Nres+1):
            d.push()
            # Coupling
            # Drawing
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(M[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)

            #Network
            count_L += 1
            L.append(line.inductor(M[i], name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))

            d.pop()
            # Series resonator
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries[i+1], 'Inductance'), fontsize=_fontsize).linewidth(1)        
            count_L += 1
            L.append(line.inductor(Lseries[i+1], name='L' + str(count_L)))

            if (i < Nres):
                d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
                count_C += 1
                C.append(line.capacitor(Cseries[i], name='C' + str(count_C)))


            # Connections
            if (i == 0):
                # Then, connect to the first inductor
                connections.append([(L[0], 1), (L[1], 0), (L[2], 0)])
                connections.append([(L[1], 1), (ground[i], 0)])
                connections.append([(L[2], 1), (C[i], 0)])
            else:
                # Then, connect to the previous capacitor
                connections.append([(C[i-1], 1), (L[2*i+1], 0), (L[2*i+2], 0)])
                connections.append([(L[2*i+1], 1), (ground[i], 0)])
                if (i < Nres):
                    # The last iteration is the coupling for the load port
                    connections.append([(L[2*i+2], 1), (C[i], 0)])

        # Drawing
        d += elm.Line().length(1).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)

        # Connections
        connections.append([(L[-1], 1), (Port2, 0)])
    else:
        # Magnetic coupling
        
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
        
        print("Cres: ", Cseries)
        print("Lp: ", Lp)
        print("M: ", M)
        
        # Source port
        # Drawing: Source port and the first line
        d += elm.Line(color='white').length(2).linewidth(0)
        d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line().length(2).linewidth(1)
        
        # Network: Port 1
        connections = [] # Network connections
        L = []
        C = []
        ground = []
        
        count_L = 0
        count_C = 0
        count_gnd = 0
        
        Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)
        
        for i in range (0, Nres):
            x = d.add(elm.Transformer(t1=4, t2=4, loop=True, core = True, fontsize=_fontsize)
                      .label(getUnitsWithScale(Lp[i], 'Inductance'), loc='left')
                      .label(getUnitsWithScale(Lp[i+1], 'Inductance'), loc='right')
                      .label("k = " + str(round(M[i]/np.sqrt(Lp[i]*Lp[i+1]), 3)), loc='top')
                      .flip())
            d += elm.Ground().at(x.p1).linewidth(1)
            d += elm.Ground().at(x.s1).linewidth(1)
            d += elm.Line().at(x.s2).length(1) 
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().length(1)
            
            # Network: The transformer is simulated using the uncoupled lumped equivalen (Zverev, Fig. 10.4 (c))
            count_L += 1
            L.append(line.inductor(Lp[i] - M[i], name='L' + str(count_L)))
            count_L += 1
            L.append(line.inductor(M[i], name='L' + str(count_L)))
            count_L += 1
            L.append(line.inductor(Lp[i+1] - M[i], name='L' + str(count_L)))

            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            count_C += 1
            C.append(line.capacitor(Cseries[i], name='C' + str(count_C)))
            
            print("L[" + str(3*i) + "] = ", getUnitsWithScale(Lp[i] - M[i], 'Inductance'))
            print("L[" + str(3*i+1) + "] = ", getUnitsWithScale(M[i], 'Inductance'))
            print("L[" + str(3*i+2) + "] = ", getUnitsWithScale(Lp[i+1] - M[i], 'Inductance'))
            print("C[" + str(i) + "] = ", getUnitsWithScale(Cseries[i], 'Capacitance'))
            
            # Connections
            if (i == 0):
                # Connect the first inductor to the source port
                connections.append([(Port1, 0), (L[0], 0)])
            else:
                # Connect the first inductor to the previous capacitor
                connections.append([(C[i-1], 1), (L[3*i], 0)])
                
            connections.append([(L[3*i], 1), (L[3*i+1], 0), (L[3*i+2], 0)])
            connections.append([(L[3*i+1], 1), (ground[i], 0)])
            connections.append([(L[3*i+2], 1), (C[i], 0)])

        x = d.add(elm.Transformer(t1=4, t2=4, loop = True, core = True, fontsize=_fontsize)
                      .label(getUnitsWithScale(Lp[-2], 'Inductance'), loc='left')
                      .label(getUnitsWithScale(Lp[-1], 'Inductance'), loc='right')
                      .label("k = " + str(round(M[-1]/np.sqrt(Lp[-2]*Lp[-1]), 3)), loc='top')
                      .flip())
        d += elm.Ground().at(x.p1).linewidth(1)
        d += elm.Ground().at(x.s1).linewidth(1)
        
        # Network: The transformer is simulated using the uncoupled lumped equivalen (Zverev, Fig. 10.4 (c))
        count_L += 1
        L.append(line.inductor(Lp[-2] - M[-1], name='L' + str(count_L)))
        count_L += 1
        L.append(line.inductor(M[-1], name='L' + str(count_L)))
        count_L += 1
        L.append(line.inductor(Lp[-1] - M[-1], name='L' + str(count_L)))
        
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        print("L[" + str(3*Nres) + "] = ", getUnitsWithScale(Lp[-2] - M[-1], 'Inductance'))
        print("L[" + str(3*Nres+1) + "] = ", getUnitsWithScale(M[-1], 'Inductance'))
        print("L[" + str(3*Nres+2) + "] = ", getUnitsWithScale(Lp[-1] - M[-1], 'Inductance'))
                
        # Load port
        d += elm.Line().at(x.s2).length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(RL) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        
        # Connections
        connections.append([(C[-1], 1), (L[-3], 0)])
        connections.append([(L[-3], 1), (L[-2], 0), (L[-1], 0)])
        connections.append([(L[-2], 1), (ground[-1], 0)])
        connections.append([(L[-1], 1), (Port2, 0)])
    
    return d, connections

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth
# Lr: Resonator inductance (it can be chosen by the user)

# References:
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 484
# [2] "Filter Handbook", Anatol I. Zverev. John Wiley and Sons, 1967, pages 562-563

def DirectCoupled_C_Coupled_SeriesResonators(gi, RS, RL, f0, BW, Lres, port_match, fstart, fstop, npoints):
    Nres = len(gi) - 2 # Number of resonators
    bw = BW / f0
    
    # Calculation of w1, w2, w - [1] 8.11-1 (15)
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
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    # Component counter
    count_C = 0
    count_L = 0
    count_gnd = 0
    
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
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize, loc='bottom').linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    # Network: Port 1
    connections = [] # Network connections
    L = []
    C = []
    ground = []
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)
    
    # First coupling
    
    if (port_match[0] == 'C'):
        # Drawing
        d += elm.Capacitor().right().label(getUnitsWithScale(Cmatch_source, 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)

        # Network
        C.append(line.capacitor(Cmatch_source, name='C' + str(count_C)))
        connections.append([(Port1, 0), (C[0], 0)])
    
    else:
        # Drawing
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lmatch_source, 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)

        # Network
        L.append(line.inductor(Lmatch_source, name='L' + str(count_L)))
        connections.append([(Port1, 0), (L[0], 0)])

    
    for i in range (0, Nres):
        # Resonator
        
        # Drawing
        d.push()
        d += elm.Capacitor().down().label(getUnitsWithScale(Cinv[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        d += elm.Ground().linewidth(1)
        
        # Network
        count_C += 1
        C.append(line.capacitor(Cinv[i], name='C' + str(count_C)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        d.pop()
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lres[i], 'Inductance'), fontsize=_fontsize).linewidth(1)
        d += elm.Capacitor().right().label(getUnitsWithScale(Cres[i], 'Capacitance'), fontsize=_fontsize).linewidth(1)
        
        count_L += 1
        L.append(line.inductor(Lres[i], name='L' + str(count_L)))
        count_C += 1
        C.append(line.capacitor(Cres[i], name='C' + str(count_C)))

        
        # Connections
        if (port_match[0] == 'C'):
            connections.append([(C[2*i], 1), (C[2*i+1], 0), (L[i], 0)])
            connections.append([(L[i], 1), (C[2*i+2], 0)])
            connections.append([(C[2*i+1], 1), (ground[i], 0)])
        else: # There's one inductance too much and one capacitor too few
            if (i == 0): # The first element must connect to the inductor
                connections.append([(L[0], 1), (C[2*i], 0), (L[i+1], 0)])
            else:
                connections.append([(C[2*i-1], 1), (C[2*i], 0), (L[i+1], 0)])
            connections.append([(L[i+1], 1), (C[2*i+1], 0)])
            connections.append([(C[2*i], 1), (ground[i], 0)])

        
    # Drawing
    d.push()
    d += elm.Capacitor().down().label(getUnitsWithScale(Cinv[-1], 'Capacitance'), fontsize=_fontsize).linewidth(1)
    d += elm.Ground().linewidth(1)
    
    count_C += 1
    C.append(line.capacitor(Cinv[-1], name='C' + str(count_C)))
    count_gnd += 1
    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
    
    d.pop()
    if (port_match[1] == 'C'):
        d += elm.Capacitor().right().label(getUnitsWithScale(Cmatch_load, 'Capacitance'), fontsize=_fontsize).linewidth(1)
        count_C += 1
        C.append(line.capacitor(Cmatch_load, name='C' + str(count_C)))
    else:
        d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lmatch_load, 'Inductance'), fontsize=_fontsize).linewidth(1)
        count_L += 1
        L.append(line.capacitor(Lmatch_load, name='L' + str(count_L)))
    
    # Load port
    # Drawing
    d += elm.Line().length(1).linewidth(1)
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize, loc='bottom').linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    # Network
    Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
    
    
    # Connections
    if (port_match[1] == 'C'):
        connections.append([(C[-3], 1), (C[-2], 0), (C[-1], 0)])
        connections.append([(C[-2], 1), (ground[-1], 0)])
        connections.append([(C[-1], 1), (Port2, 0)])
    else:
        connections.append([(C[-2], 1), (C[-1], 0), (L[-1], 0)])
        connections.append([(C[-1], 1), (ground[-1], 0)])
        connections.append([(L[-1], 1), (Port2, 0)])

   
    return d, connections


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

        # Array of components
    J = []
    
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
    return RS, qw, Lres, Cres

# gi: Normalized lowpass coefficients
# RS: Source impedance
# RL: Load impedance
# f0: Center frequency
# BW: Bandwidth

# Reference: 
# [1] "Microwave Filters, Impedance-Matching Networks, and Coupling Structures", George L. Matthaei, L. Young, E. M. Jones, Artech House pg. 482
def DirectCoupled_QW_Coupled_ShuntResonators(gi, RS, RL, f0, BW, fstart, fstop, npoints):
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
    Y0 = 1/RS
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing()
    _fontsize = 12
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    # Component counter
    count_C = 0
    count_L = 0
    count_TL = 0
    count_gnd = 0
    
    # Array of components
    J = []
    
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
    
        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    # Network: Port 1
    connections = [] # Network connections
    L = []
    C = []
    TL = []
    ground = []
    
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)
    
    # Quarter wavelength line
    beta = freq.w/rf.c
    Z0_line = rf.media.DefinedGammaZ0(frequency=freq, Z0=RS, gamma=0+beta*1j)
    
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
        C.append(line.capacitor(Cres[i], name='C' + str(count_C)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        count_L += 1
        L.append(line.inductor(Lres[i], name='L' + str(count_L)))
        count_gnd += 1
        ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
        
        # Coupling line
        # Drawing
        d.pop()
        d += elm.Line().right().length(2).linewidth(1)
        d += TransmissionLine().right().label("l = " + getUnitsWithScale(qw, 'Distance'), fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(RS) + " \u03A9 ", loc = 'top').linewidth(1)
        d += elm.Line().right().length(2).linewidth(1)
        
        count_TL += 1
        TL.append(Z0_line.line(Z0_line.theta_2_d(90, deg=True), unit='m', name='TL' + str(count_TL)))
        
        if (i == 0):
            # Connect to the source port
            connections.append([(Port1, 0), (L[0], 0), (C[0], 0), (TL[0], 0)])
        else:
            # Connect to the previous TL
            connections.append([(TL[i-1], 1), (L[i], 0), (C[i], 0), (TL[i], 0)])
            
        connections.append([(C[i], 1), (ground[2*i], 0)])
        connections.append([(L[i], 1), (ground[2*i+1], 0)])          
        
    # Load port
    # Drawing
    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    # Network
    Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
    
    # Connections
    connections.append([(Port2, 0), (TL[-1], 1)])
       
    return d, connections