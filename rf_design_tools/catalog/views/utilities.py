import numpy as np

def ArrayToString(arr):
    string=''
    for x in arr:
        string += str(x) + ";"
    return string[:-1]

# Ported from Qucs num2str() function
def getUnitsWithScale(value, units, n_decimals=2):
    c = ''
    cal = abs(value)
    Expo = -5
    if(cal > 1e-20):
        cal = np.log10(cal) / 3.0
        if(cal < -0.2):
            cal -= 0.98;
        Expo = int(cal);
        
    if (Expo == -5): c = 'f'
    elif (Expo == -4): c = 'p'
    elif (Expo == -3): c = 'n'
    elif (Expo == -2): c = 'u'
    elif (Expo == -1): c = 'm' 
    elif (Expo == 1): c = 'k'
    elif (Expo == 2): c = 'M'
    elif (Expo == 3): c = 'G'
    elif (Expo == 4): c = 'T'
        
    if (c!=''):
        value /= pow(10.0, (3.*Expo))
    value = float(("{:." + str(n_decimals) + "f}").format(value))
        
    # Add units
    if (units == "Capacitance"):
        return str(value) + " " + c + "F"
    elif (units == "Inductance"): return str(value) + " " + c + "H"
    elif(units == "Distance"): return str(value) + " " + c + "m"
    elif(units == "Frequency"): return str(value) + " " + c + "Hz"
    elif(units == "Impedance"): return str(value) + " " + c + "\u03A9"
    elif(units == "Resistance"): return str(value) + " " + c + "\u03A9"
    elif(units == "Power"): return str(value) + " " + c + "W"

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]