import numpy as np

# Get the ABCD matrix of a ladder element
def get_ABCD_Matrix_Ladder_Element(code, x, w):
    x = np.atleast_1d(x)
    if (code == 'LS'):
        T = np.array([[1, 1j*w*x[0]], [0, 1]]);
    elif (code == 'LP'):
        T = np.array([[1, 0], [1/(1j*w*x[0]), 1]]);
    elif (code == 'CS'):
        T =  np.array([[1, 1/(1j*w*x[0])], [0, 1]]);
    elif (code == 'CP'):
        T =  np.array([[1, 0], [1j*w*x[0], 1]]);
    elif (code == 'CASTL'):# x[0]: Z0, x[1]: theta
        x[1] *= np.pi/180 
        T =  np.array([[np.cos(x[1]), x[0]*np.sin(x[1])], [np.sin(x[1])/x[0], np.cos(x[1])]]);
    elif (code == 'SPR'): # Series Parallel Resonator
        ZL = 1j*w*x[0]
        ZC = 1/(1j*w*x[1])
        Zres = (ZL*ZC/(ZL+ZC))
        T = np.array([[1, Zres], [0, 1]])
    elif (code == 'SSR'): # Shunt Series Resonator
        ZL = 1j*w*x[0]
        ZC = 1/(1j*w*x[1])
        Zres = (ZL+ZC)
        T = np.array([[1, 0], [1/Zres, 1]])
    elif (code == 'DSPR'): # Double Series Parallel Resonator (Elliptic BPF)
        ZL_ser = 1j*w*x[0]
        ZC_ser = 1/(1j*w*x[1])
        ZL_par = 1j*w*x[2]
        ZC_par = 1/(1j*w*x[3])

        Zser = ZL_ser + ZC_ser
        Zpar = (ZL_par*ZC_par)/(ZL_par + ZC_par)
        Zres = (Zser*Zpar)/(Zser + Zpar)
        T = np.array([[1, Zres], [0, 1]])

    elif (code == 'DSPSR'): # Double Series Parallel Shunt Resonator (Elliptic BPF)
        ZL_par = 1j*w*x[0]
        ZC_par = 1/(1j*w*x[1])
        ZL_ser = 1j*w*x[2]
        ZC_ser = 1/(1j*w*x[3])

        Zpar = (ZL_par*ZC_par)/(ZL_par + ZC_par)
        Zser = ZL_ser + ZC_ser
        Zres = Zpar + Zser
        T = np.array([[1, 0], [1/Zres, 1]])
    return T


def get_ABCD_Network(code, x, freq):
    m = freq.size;

    T_vs_f = np.empty((m, 2, 2), dtype=complex); # Array of m (2x2)-matrices
    for i in range(0, m): # Frequency loop      
        k = 0;
        for block in code: # Get ABCD for one frequency
            Tk = get_ABCD_Matrix_Ladder_Element(block, x[k], 2*np.pi*freq[i]);

            if (k == 0):
                T = Tk;
            else:
                T = np.matmul(T, Tk);
                
            k += 1;  
        T_vs_f[i] = T; # Store ABCD matrix for the i-th frequency
        
    return T_vs_f

# Get S-parameters
def get_SPAR(ZS, ZL, code, x, freq):
    T = get_ABCD_Network(code, x, freq); # ABCD matrix calculation vs freq
    S = TtoS(T, ZS, ZL); # S-parameter matrix conversion
    
    return S


# IEEE Transactions on Microwave Theory and Techniques. Vol 42, No 2. February 1994.
# Conversions Between S, Z, Y, h, ABCD, and T Parameters which are Valid for Complex Source and Load Impedances.
# ABCD to S parameter matrix conversion
def TtoS(M, Z1, Z2):
    # Get the number of frequency samples
    dimensions = M.shape;
    
    if (len(dimensions) == 3):
        n_freq = M.shape[0];
        if (len(Z1) == 1):
            Z1 = Z1*np.ones(n_freq);
        if (len(Z2) == 1):
            Z2 = Z2*np.ones(n_freq);
    else:
        n_freq = 1;
        Z1 = np.array([Z1]);
        Z2 = np.array([Z2]);
        
    S = np.empty((n_freq, 2, 2), dtype=complex); # Array of m (2x2)-matrices
    for i in range(0, n_freq):
       
        T = M[i];
 
        S11 = T[0,0]*Z2[i] + T[0,1] - T[1,0]*np.conj(Z1[i])*Z2[i] - T[1,1]*np.conj(Z1[i]);
        S12 = np.linalg.det(T) * 2 * np.sqrt(np.real(Z1[i])*np.real(Z2[i]));
        S21 = 2*np.sqrt(np.real(Z1[i])*np.real(Z2[i]))
        S22 = -T[0,0]*np.conj(Z2[i]) + T[0,1] - T[1,0]*Z1[i]*np.conj(Z2[i]) + T[1,1]*np.conj(Z1[i]);
        
        den = T[0,0]*Z2[i] + T[0,1] + T[1,0]*Z1[i]*Z2[i] + T[1,1]*Z1[i]
        
        S[i] = np.array([[S11/den, S12/den], [S21/den, S22/den]]);
    
    return S

# S to ABCD parameter matrix conversion
def StoT(M, Z1, Z2):
    # Get the number of frequency samples
    dimensions = M.shape;
    if (len(dimensions) == 3):
        n_freq = M.shape[0];
    else:
        n_freq = 1;
        Z1 = np.array([Z1]);
        Z2 = np.array([Z2]);
        
    T = np.empty((n_freq, 2, 2), dtype=complex); # Array of m (2x2)-matrices
    for i in range(0, n_freq):
     
        S = M[i];

        A = (np.conj(Z1[i])+S[0,0]*Z1[i])*(1-S[1,1]) + S[1,0]*S[0,1]*Z1[i];
        B = (np.conj(Z1[i])+S[0,0]*Z1[i])*(np.conj(Z2[i])+S[1,1]*Z2[i])-S[1,0]*S[0,1]*Z1[i]*Z2[i]
        C = (1 - S[0,0])*(1 - S[1,1])-S[0,1]*S[1,0]
        D = (1 - S[0,0])*(np.conj(Z2[i]) + S[1,1]*Z2[i]) + S[0,1]*S[1,0]*Z2[i];
    
        den = 2*S[1,0]*np.sqrt(np.real(Z1[i]) * np.real(Z2[i]))
    
        T[i] = np.array([[A/den, B/den], [C/den, D/den]]);
    
    return T
