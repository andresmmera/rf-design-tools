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
# 'Microwave Engineering'. David Pozar. John Wiley and Sons. 4th Edition. Pg 252-256


def BinomialCoeffs(n, k):
  coeff = 1
  for i in range(1, k+1):
    coeff *= (n + (1 - i)) / (1.0 * i)
  
  return coeff




def synthesize_MultiSection_TL_Transformer_Matching_Network(params):

    RS = params['RS']
    RL = params['RL']
    gamma_max = params['gamma_max']
    N = params['N']
    Weighting = params['Weighting']

    Z = []
    Zaux = RS

    if (Weighting == '1'): 
        # Binomial
        
        for i in range(1, N+1):
            Ci = BinomialCoeffs(N - 1, i - 1)
            Zi = np.exp(np.log(Zaux) + (Ci / pow(2, N - 1)) * np.log(RL / RS))
            Zaux = Zi
            Z.append(Zi)

    else:
        # Chebyshev
        w = []
        if (np.abs(np.log(RL / RS) / (2 * gamma_max)) < 1):
            sec_theta_m = 0
        else:
            sec_theta_m = np.cosh((1 / (1. * N)) * np.arccosh(np.abs(np.log(RL / RS) / (2 * gamma_max))))

            if (N == 1):
                w.append(sec_theta_m)
            elif(N == 2):
                w.append(sec_theta_m * sec_theta_m)
                w.append(2 * (sec_theta_m * sec_theta_m - 1))
            elif(N == 3):
                w.append(sec_theta_m**3)
                w.append(3 * (sec_theta_m**3 - sec_theta_m))
                w.append(w[1])
            elif(N == 4):
                w.append(sec_theta_m**4)
                w.append(4 * sec_theta_m * sec_theta_m * (sec_theta_m * sec_theta_m - 1))
                w.append(2 * (1 - 4 * sec_theta_m * sec_theta_m + 3 * pow(sec_theta_m, 4)))
                w.append(w[1])
            elif(N == 5):
                w.append(sec_theta_m**5)
                w.append(5 * (sec_theta_m**5 - sec_theta_m**3))
                w.append(10 * sec_theta_m**5 - 15 * sec_theta_m**3 + 5 * sec_theta_m)
                w.append(w[2])
                w.append(w[1])
            elif(N == 6):
                w.append(sec_theta_m**6)
                w.append(6 * sec_theta_m**4 * (sec_theta_m * sec_theta_m - 1))
                w.append(15 * sec_theta_m**6 - 24 * sec_theta_m**4 + 9 * sec_theta_m * sec_theta_m)
                w.append(2 * (10 * sec_theta_m**6 - 18 * sec_theta_m**4 + 9 * sec_theta_m * sec_theta_m - 1))
                w.append(w[2])
                w.append(w[1])
            elif(N == 7):
                w.append(sec_theta_m**7)
                w.append(7 * sec_theta_m**5 * (sec_theta_m * sec_theta_m - 1))
                w.append(21 * sec_theta_m**7 - 35 * sec_theta_m**5 + 14 * sec_theta_m**3)
                w.append(35 * sec_theta_m**7 - 70 * sec_theta_m**5 + 42 * sec_theta_m**3 - 7 * sec_theta_m)
                w.append(w[3])
                w.append(w[2])
                w.append(w[1])

            for i in range(N):
                if (RL < RS):
                    Zi = np.exp(np.log(Zaux) - gamma_max * w[i])
                else:
                    Zi = np.exp(np.log(Zaux) + gamma_max * w[i])
                Z.append(Zi)
                Zaux = Zi
    return Z

def MultiSection_TL_Transformer_MatchingNetwork(params):

    RS = params['RS']
    RL = params['RL']
    XL = params['XL']
    N = params['N']
    f0 = params['f0']

    fstart = params['f_start']
    fstop = params['f_stop']
    npoints = params['n_points']  
       
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
       
    Z = synthesize_MultiSection_TL_Transformer_Matching_Network(params)

    NetworkType = {}
    comp_val = {}
    NetworkType['freq'] = (np.linspace(fstart, fstop, npoints))
    NetworkType['Network'] = 'TL_Transformer'
    comp_val['ZS'] = RS
    comp_val['ZL'] = RL
    comp_val['f0'] = f0
    comp_val['N'] = N
    
    x = []
    topology = []

        
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(1).linewidth(1)
    
    for i in range(N):
        # Drawing
        d += TransmissionLine().right().label("l = " + str(90) + " deg", fontsize=_fontsize, loc = 'bottom').label("Z\u2080 = " + str(round(Z[i],1)) + " \u03A9 ", loc = 'top', fontsize=_fontsize).linewidth(1)
        d += elm.Line().right().length(1).linewidth(1)

        # Network
        comp_val['Z'+str(i+1)] = Z[i]


    d += elm.Line().right().length(1).linewidth(1)
        
    if (XL == 0):
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) +  "\u03A9", fontsize=_fontsize).linewidth(1)

    else:
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + "+j·" + str(float("{:.2f}".format(XL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)

    return d, NetworkType, comp_val