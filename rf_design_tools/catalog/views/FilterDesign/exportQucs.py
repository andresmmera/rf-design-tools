# Get units with scale, etc.
from skrf import setup_pylab
from ..utilities import *
from datetime import date

# Import functions for filter synthesis
from .DirectCoupledFilters import synthesize_DC_Filter_C_Coupled_Shunt_Resonators
from .DirectCoupledFilters import synthesize_DC_Filter_L_Coupled_Shunt_Resonators
from .DirectCoupledFilters import synthesize_DC_Filter_QW_Shunt_Resonators

# This function exports the filter as a Qucs schematic
def getCanonicalFilterQucsSchematic(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
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

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    xtext = 17
    ytext = -26

    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Order " + str(N) + " Filter"
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source port
    x_padding = 0
    if ((Mask == 'Lowpass') or (Mask == 'Highpass')):
        x_step_LPF = 100 # Spacing
        if (FirstElement == 1): # First shunt - additional padding is needed because of the text of the first element
            x_padding = 60
        ys = y+30
    elif(Mask == 'Bandpass'):
        x_step_BPF = 100 # Spacing
        ys = y+60
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    else: # Bandstop
        x_step_BSF = 130 # Spacing
        ys = y+120
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = ys - 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
    components += "<Pac P1 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"1\" 1 \"" + str(ZS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"

    x += x_padding
    
    # Draw the filter components
    for i in range(N):

        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):    
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                x += x_step_LPF
                C = getUnitsWithScale(gi[i+1]/(ZS*w0), 'Capacitance')
                count_C += 1
                xtext = 17
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+30) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+60) + " 0 0 0 0>\n"


                x1  = x - (x_step_LPF - 30) # 30 = len(inductor)/2
                x2 = x
                y1 = y
                y2 = y

                if (i == 0):# The first element is shunt and some padding was added
                    if (FirstElement == 1):
                        x1 -= x_padding + 30

                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            elif (Mask == 'Highpass'):
                x += x_step_LPF
                L = getUnitsWithScale(ZS/(gi[i+1]*w0), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+30) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+60) + " 0 0 0 0>\n"
                
                x1  = x - (x_step_LPF - 30) # 30 = len(inductor)/2
                x2 = x
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandpass'):
                step = x_step_BPF
                if ((i == 0) and (FirstElement == 1)):
                    step += 60 # Additional spacing if the first element is shunt
                if (FirstElement == 2):
                    step += 100
                
                x += step
                x -= 30
                C = getUnitsWithScale(gi[i+1]/(ZS*Delta), 'Capacitance')
                count_C += 1
                xtext = -100
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"

                x += 60
                L = getUnitsWithScale(ZS*Delta/(gi[i+1]*w0*w0), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"

                # To the previous element
                if (i == 0):
                    x1  = x-step-30; x2 = x-30; y1 = y; y2 = y # +100 because x is at the center of the series resonator
                else:
                    x1  = x-step+100; x2 = x-30; y1 = y; y2 = y # +100 because x is at the center of the series resonator
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Vertical line
                x1  = x-30; x2 = x-30; y1 = y; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the left
                x1  = x-30; x2 = x-60; y1 = ys-30; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the right
                x1  = x-30; x2 = x; y1 = ys-30; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the right (upper)
                x1  = x-30; x2 = x; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandstop'):
                x += x_step_BSF
                L = getUnitsWithScale(ZS/(gi[i+1]*Delta), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                
                C = getUnitsWithScale(gi[i+1]*Delta/(ZS*w0*w0), 'Capacitance')
                count_C += 1
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(ys+90) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(ys+120) + " 0 0 0 0>\n"

                # Inductor to the mainline
                x1  = x; x2 = x; y1 = ys-30; y2 = ys-60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between capacitor and inductor
                x1  = x; x2 = x; y1 = ys+30; y2 = ys+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the previous element
                if (i == 0):
                    x1  = x-x_step_BSF; x2 = x; y1 = y+60; y2 = y+60
                else:
                    x1  = x-x_step_BSF+30; x2 = x; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                
        else:
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                x += x_step_LPF
                L = getUnitsWithScale(ZS*gi[i+1]/w0, 'Inductance')
                count_L += 1
                xtext = -40
                ytext = -60
                components += "<L L"+ str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                x1  = x - x_step_LPF
                x2 = x - 30 # len(inductor)/2
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Highpass'):
                x += x_step_LPF
                C = getUnitsWithScale(1/(gi[i+1]*w0*ZS), 'Capacitance')
                count_C += 1
                xtext = -40
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                x1  = x - x_step_LPF
                x2 = x - 30 # len(inductor)/2
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandpass'):
                x += x_step_BPF

                C = getUnitsWithScale(Delta/(ZS*w0*w0*gi[i+1]), 'Capacitance')
                count_C += 1
                xtext = -40
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                L = getUnitsWithScale(ZS*gi[i+1]/(Delta), 'Inductance')
                count_L += 1
                xtext = -40
                ytext = -60
                components += "<L L"+ str(count_L) + " 1 " + str(x+100) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                # To the previous section
                x1  = x-x_step_BPF; x2 = x-30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between inductor and capacitor
                x1  = x+30; x2 = x+70; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandstop'):
                x += x_step_BSF
                L = getUnitsWithScale(gi[i+1]*ZS*Delta/(w0*w0), 'Inductance')
                count_L += 1
                xtext = -30; ytext = 10
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                C = getUnitsWithScale(1/(ZS*Delta*gi[i+1]), 'Capacitance')
                count_C += 1
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                # Between first node and inductor
                x1  = x-60; x2 = x-30; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between first node and capacitor
                x1  = x-60; x2 = x-30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # First node
                x1  = x-60; x2 = x-60; y1 = y; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between second node and inductor
                x1  = x+60; x2 = x+30; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between second node and capacitor
                x1  = x+60; x2 = x+30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Second node
                x1  = x+60; x2 = x+60; y1 = y; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the previous element
                x1  = x-x_step_BSF; x2 = x-60; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Mask == 'Lowpass') or (Mask == 'Highpass')):
        x_last = 100 # Additional padding
        x1 = x 
        if (((FirstElement == 2) and (N % 2 == 1)) or ((FirstElement == 1) and (N % 2 == 0))):
            x1 += 30
        else:
            x_last += 30 # Extra padding is needed for the text of the last element

        x += x_last # Position of the port

        x2 = x
        y1 = y
        y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    elif (Mask == 'Bandpass'):
        x_last = 200
        if (((FirstElement == 1) and (N % 2 == 1)) or ((FirstElement == 2) and (N % 2 == 0))):
            x1 = x
            x_last -= 50
        else:
            x1  = x+130
        
        # To the load port
        x2 = x+x_last; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
        x += x_last
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    else: # Bandstop
        x_last = x_step_BSF
        if (((FirstElement == 1) and (N % 2 == 1)) or ((FirstElement == 2) and (N % 2 == 0))):
            x1 = x
            x_last += 30
        else:
            x1  = x+60
        
        # To the load port
        x2 = x+x_last; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
        x += x_last
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = ys-60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    xtext = 17
    ytext = -26
    RL = round(ZS*gi[-1], 2)
    components += "<Pac P2 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"


    # S-parameter simulation block
    x_block = 60
    y_block = ys + 150
    components += "<.SP SP1 1 " + str(x_block) + " " + str(y_block) + " 0 67 0 0 \"lin\" 1 \"" + str(f_start) + " MHz \" 1 \"" + str(f_stop) + " MHz \" 1 \"" + str(n_points) + "\" 1 \"no\" 0 \"1\" 0 \"2\" 0>\n"
    components += "<Eqn Eqn1 1 " + str(x_block + 200) + " " + str(y_block) + " -28 15 0 0 \"S21_dB=dB(S[2,1])\" 1 \"S11_dB=dB(S[1,1])\" 1 \"S22_dB=dB(S[2,2])\" 1 \"yes\" 0>\n"
    components += "<Eqn Eqn2 1 " + str(x_block + 400) + " " + str(y_block) + " -28 15 0 0 \"gd=groupdelay(S,2,1)\" 1 \"phase=(180/pi)*angle(S[2,1])\" 1 \"yes\" 0>\n"

    # Close components and wire blocks
    components += "</Components>\n"
    wires += "</Wires>\n"

    # Text
    y_title = str(50)
    paintings = "<Paintings>\n"

    copyright = " - Copyright \u00A9 2020-" + str(today.year) + " Andrés Martínez Mera - GNU Public License Version 3"
    if ((Response == 'Chebyshev')):
        paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" + Response + " Order " + str(N) + " " + Mask + " Filter, Ripple " + str(Ripple) + " dB "
                + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")
    else:
        paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" + Response + " Order " + str(N) + " " + Mask + " Filter, "
                + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")
    

    # Diagrams
    x_size = 400
    y_size = 300
    x_pos = 170
    y_pos = ys + 650
    diagrams = "<Diagrams>\n"
    # Response
    paintings += ("<Text " + str(x_pos + round(x_size/2) - 50) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Response\">\n")
    diagrams += ("<Rect " + str(x_pos) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 0 -50 5 5 1 -0.1 0.5 1.1 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"S21_dB\" #ff0000 0 3 0 0 0>\n")
    diagrams += str("<\"S11_dB\" #0000ff 0 3 0 0 0>\n")
    diagrams += "</Rect>\n"
    
    # Group Delay and phase
    paintings += ("<Text " + str(x_pos + x_size + 100 + round(x_size/2) - 120) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Group Delay and Phase\">\n")
    diagrams += ("<Rect " + str(x_pos + x_size + 100 ) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 1 -4 1 4 0 -180 90 180 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"gd\" #0000ff 0 3 0 0 0>\n")
    diagrams += str("<\"phase\" #00aa00 0 3 0 0 1>\n")
    diagrams += "</Rect>\n"

    diagrams += "</Diagrams>\n"
    paintings += "</Paintings>\n"

    schematic += components
    schematic += wires
    schematic += paintings
    schematic += diagrams
    
    return schematic

# This function exports the filter as a Qucs schematic. Depending on the filter type it delegates the task into another function.
def getEllipticFilterQucsSchematic(params):
    Mask = params['Mask']
    FirstElement = params['FirstElement']

    if (FirstElement == 1): # First shunt
        if (Mask == 'Lowpass'):
            QucsSchematic = getLowpassEllipticFirstShuntFilterQucsSchematic(params)
        elif(Mask == 'Highpass'):
            QucsSchematic = getHighpassEllipticFirstShuntFilterQucsSchematic(params)
        elif(Mask == 'Bandpass'):
            QucsSchematic = getBandpassEllipticFirstShuntFilterQucsSchematic(params)
        elif(Mask == 'Bandstop'):
            QucsSchematic = getBandstopEllipticFirstShuntFilterQucsSchematic(params)
    else: # First series
        if (Mask == 'Lowpass'):
            QucsSchematic = getLowpassEllipticFirstSeriesFilterQucsSchematic(params)
        elif(Mask == 'Highpass'):
            QucsSchematic = getHighpassEllipticFirstSeriesFilterQucsSchematic(params)
        elif(Mask == 'Bandpass'):
            QucsSchematic = getBandpassEllipticFirstSeriesFilterQucsSchematic(params)
        elif(Mask == 'Bandstop'):
            QucsSchematic = getBandstopEllipticFirstSeriesFilterQucsSchematic(params)

    return QucsSchematic

# This function exports the first series elliptic LPF
def getLowpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 17
    ytext_lower = -26

    # Position of the text in the upper branch components
    xtext_upper = -35
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    step = 90

    for i in range(N):
            
        x += step
        ## Series inductor
        L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cshunt[i], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Shunt capacitor
        count_C += 1
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS) * Lseries[i], 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Capacitor to mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous component
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Shunt inductor

            L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cseries[i], 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

            # Wire to the capacitor
            x1 = x; x2 = x; y1 = y+120; y2 = y+90
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x; x2 = x+step+30; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cshunt[-1], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step+30; x2 = x; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# This function exports the first series elliptic LPF
def getHighpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 17
    ytext_lower = -26

    # Position of the text in the upper branch components
    xtext_upper = -35
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    step = 90

    for i in range(N):
            
        x += step
        ## Series capacitor
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cshunt[i]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Shunt inductor
        count_L += 1
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Lseries[i]), 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Capacitor to mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous component
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Shunt capacitor
            C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cseries[i]), 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

            # Wire to the capacitor
            x1 = x; x2 = x; y1 = y+120; y2 = y+90
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x; x2 = x+step+30; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cshunt[-1]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step+30; x2 = x; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic


# This function exports the first shunt elliptic LPF
def getLowpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N > 7):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Wire to the mainline
    x1 = x; x2 = x+80; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 90

    for i in range(N):
            
        x += step
        ## Shunt capacitor
        C = getUnitsWithScale(Cshunt[i] / (2 * np.pi * fc * RS), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"


        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (i > 0):
            # Node to the previous series inductor
            x1 = x-step+30; x2 = x; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Series inductor
        count_L += 1
        L = getUnitsWithScale(Lseries[i] * RS / (2 * np.pi * fc), 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Current inductor to node
        x1 = x-30; x2 = x-step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Series capacitor
            C = getUnitsWithScale(Cseries[i] / (2 * np.pi * fc * RS), 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Current capacitor to node
            x1 = x-30; x2 = x-step; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x+30; x2 = x+90; y1 = y+60; y2 = y+60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        C = getUnitsWithScale(Cshunt[-1]/ (2 * np.pi * fc * RS), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series inductor
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step-60; x2 = x; y1 = y+60; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic


# This function exports the first shunt elliptic LPF
def getHighpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N > 7):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Wire to the mainline
    x1 = x; x2 = x+80; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 90

    for i in range(N):
        x += step
        ## Shunt inductor
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Cshunt[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"


        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (i > 0):
            # Node to the previous series inductor
            x1 = x-step+30; x2 = x; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Series capacitor
        count_C += 1
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Lseries[i]), 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Current inductor to node
        x1 = x-30; x2 = x-step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Series inductor
            L = getUnitsWithScale(RS / (2 * np.pi * fc * Cseries[i]), 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Current capacitor to node
            x1 = x-30; x2 = x-step; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        else:
            x1 = x+30; x2 = x+90; y1 = y+60; y2 = y+60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Cshunt[-1]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series inductor
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step-60; x2 = x; y1 = y+60; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# This function exports the first shunt elliptic LPF
def getBandpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 200 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x+110; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 140

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    for i in range(N):
        x += step
        # Shunt parallel resonator
        L = getUnitsWithScale(Kl * delta / (Cshunt[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x-60) + " " + str(y+180) + " 0 0 0 0>\n"

        C = getUnitsWithScale(Cshunt[i] * Kc / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x+60) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt inductor to node
        x1 = x - 60; x2 = x - 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Shunt capacitor to node
        x1 = x + 60; x2 = x + 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire between capacitor and inductor
        x1 = x - 60; x2 = x; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x + 60; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x; x2 = x; y1 = y + 100; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the previous section
        x1 = x - 80; x2 = x; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Upper branch series resonator
        count_L += 1
        L = getUnitsWithScale(Kl * Lseries[i] / delta, 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        x += step
        count_C += 1
        C = getUnitsWithScale(Kc * delta / Lseries[i], 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wire between capacitor and inductor
        x1 = x-step+30; x2 = x-30; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire from the series inductor to the node
        x1 = x-step-30; x2 = x-step-60; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step-60; x2 = x-2*step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire from the series capacitor to the next node
        x1 = x+30; x2 = x+60; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            # Upper-branch parallel resonator
            offset = round(0.5*step)
            L = getUnitsWithScale(Kl * delta / Cseries[i], 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x-offset) + " " + str(y+20) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            C = getUnitsWithScale(Kc * Cseries[i] / delta, 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x-offset) + " " + str(y-60) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Wire from the parallel inductor to the previous node
            x1 = x-offset-30; x2 = x-step-60; y1 = y + 20; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-step-60; x2 = x-step-60; y1 = y + 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel capacitor to the previous node
            x1 = x-offset-30; x2 = x-step-60; y1 = y - 60; y2 = y - 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-step-60; x2 = x-step-60; y1 = y - 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel inductor to the next node
            x1 = x-offset+30; x2 = x+60; y1 = y + 20; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y + 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel capacitor to the next node
            x1 = x-offset+30; x2 = x+60; y1 = y - 60; y2 = y - 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y - 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        else:
            # Wire from the parallel capacitor to the next node
            x1 = x+60; x2 = x+step; y1 = y + 60; y2 = y + 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            
    
    
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step        
        # Lower-branch parallel resonator
        L = getUnitsWithScale(Kl * delta / (Cshunt[-1]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x-60) + " " + str(y+180) + " 0 0 0 0>\n"

        C = getUnitsWithScale(Cshunt[-1] * Kc / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x+60) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt inductor to node
        x1 = x - 60; x2 = x - 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Shunt capacitor to node
        x1 = x + 60; x2 = x + 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire between capacitor and inductor
        x1 = x - 60; x2 = x; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x + 60; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x; x2 = x; y1 = y + 100; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the previous section
        x1 = x - 80; x2 = x; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x1 = x; x2 = x+step; y1 = y+60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x-60; x2 = x; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

def getBandpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 170 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -37
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    x += 50
    step = 180

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x+step-90; y1 = y; y2 = y 
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    for i in range(N):
        x += step
        
        # Upper-brach series resonator
        L = getUnitsWithScale(Kl * Cshunt[i] / delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * delta / Cshunt[i], 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    
        # Wire between inductor and capacitor
        x1 = x-30; x2 = x+30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x+90; x2 = x+step; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the next section
        x1 = x+step; x2 = x+step+90; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        # Lower-branch parallel resonator
        L = getUnitsWithScale(Kl * delta / Lseries[i], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+80) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * Lseries[i] / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+80) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wires between the parallel resonator
        x1 = x-60; x2 = x-60; y1 = y+50; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y+50; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x; y1 = y+30; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x; y1 = y+30; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):

            # Wires to the series resonator
            x1 = x-60; x2 = x-60; y1 = y+110; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y+110; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-60; x2 = x; y1 = y+130; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x; y1 = y+130; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x; x2 = x; y1 = y+130; y2 = y+160
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


            # Lower-branch series resonator
            L = getUnitsWithScale(Kl * Cseries[i] / delta, 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+190) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            C = getUnitsWithScale(Kc * delta / Cseries[i], 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+270) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y + 300) + " 0 0 0 0>\n"

            # Wires between capacitor and inductor
            x1 = x; x2 = x; y1 = y+220; y2 = y+240
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            components += "<GND *1 5 " + str(x-60) + " " + str(y + 110) + " 0 0 0 0>\n"
            components += "<GND *1 5 " + str(x+60) + " " + str(y + 110) + " 0 0 0 0>\n"

    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step
        # Last upper-branch series resonator
        L = getUnitsWithScale(Kl * Cshunt[-1] / delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * delta / Cshunt[-1], 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    
        # Wire between inductor and capacitor
        x1 = x-30; x2 = x+30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Source
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wires to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x-step+90; y1 = y; y2 = y 
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

def getBandstopEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 200 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -37
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    x += 50
    step = 130

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


    for i in range(N):
        x += step
        
        # Upper-brach parallel resonator
        L = getUnitsWithScale(Kl * Cshunt[i] * delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+40) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc / (delta * Cshunt[i]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y-40) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    
        # Wires to the previous node
        x1 = x-60; x2 = x-30; y1 = y+40; y2 = y+40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-30; y1 = y-40; y2 = y-40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-60; y1 = y-40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-60; y1 = y+40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step; x2 = x-60; y1 = y; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wires to the next node
        x1 = x+60; x2 = x+30; y1 = y+40; y2 = y+40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+30; y1 = y-40; y2 = y-40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y-40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y+40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+step; x2 = x+60; y1 = y; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
       
        x += step
        # Lower-branch series resonator
        L = getUnitsWithScale(Kl / (delta * Lseries[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * Lseries[i] * delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+140) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wire between components
        x1 = x; x2 = x; y1 = y+90; y2 = y+110 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):

            # Lower-branch parallel resonator
            L = getUnitsWithScale(Kl * delta * Cseries[i], 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+230) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x-60) + " " + str(y + 260) + " 0 0 0 0>\n"

            C = getUnitsWithScale(Kc / (Cseries[i] * delta), 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+230) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x+60) + " " + str(y + 260) + " 0 0 0 0>\n"

            # Wires to the node
            x1 = x-60; x2 = x-60; y1 = y+200; y2 = y+180
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y+200; y2 = y+180
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x; y1 = y+180; y2 = y+180
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-60; x2 = x; y1 = y+180; y2 = y+180
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x; x2 = x; y1 = y+180; y2 = y+170
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        else:
            components += "<GND *1 5 " + str(x) + " " + str(y + 170) + " 0 0 0 0>\n"


    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step
        # Last upper-branch parallel resonator
        L = getUnitsWithScale(Kl * Cshunt[-1] * delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+40) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc / (delta * Cshunt[-1]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y-40) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
 
        # Wires to the previous node
        x1 = x-60; x2 = x-30; y1 = y+40; y2 = y+40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-30; y1 = y-40; y2 = y-40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-60; y1 = y-40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x-60; y1 = y+40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step; x2 = x-60; y1 = y; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wires to the next node
        x1 = x+60; x2 = x+30; y1 = y+40; y2 = y+40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+30; y1 = y-40; y2 = y-40 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y-40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y+40; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+step; x2 = x+60; y1 = y; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    else:
        x1 = x; x2 = x+step; y1 = y; y2 = y 
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        RL = round(RL, 2)

    # Source
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wires to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

def getBandstopEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 230 # Current x-position in the schematic
    y = 280 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    step = 140# x-axis step

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    x1 = x; x2 = x+step; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    for i in range(N):
        x += step
        # Lower-branch series resonator
        L = getUnitsWithScale(Kl / (delta * Cshunt[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * Cshunt[i] * delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Wire between components
        x1 = x; x2 = x; y1 = y+90; y2 = y+120
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Upper-branch parallel resonator
        count_L += 1
        L = getUnitsWithScale(Kl * Lseries[i] * delta, 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        count_C += 1
        C = getUnitsWithScale(Kc / (delta * Lseries[i]), 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y-70) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wires to the previous node
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step; x2 = x-30; y1 = y-70; y2 = y-70
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step; x2 = x-step; y1 = y-70; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wires to the next node
        x1 = x+step; x2 = x+30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+step; x2 = x+30; y1 = y-70; y2 = y-70
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+step; x2 = x+step; y1 = y-70; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            # Upper-branch series resonator
            offset = round(0.5*step)
            L = getUnitsWithScale(Kl / (Cseries[i] * delta), 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x-offset) + " " + str(y-120) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            C = getUnitsWithScale(Kc * delta * Cseries[i], 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x+offset) + " " + str(y-120) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Wires to the previous node
            x1 = x-step; x2 = x-offset-30; y1 = y-120; y2 = y-120
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-step; x2 = x-step; y1 = y-120; y2 = y-70
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wires between components
            x1 = x-offset+30; x2 = x+offset-30; y1 = y-120; y2 = y-120
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wires to the next node
            x1 = x+offset+30; x2 = x+step; y1 = y-120; y2 = y-120
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+step; x2 = x+step; y1 = y-120; y2 = y-70
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


            
    
    
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step        
        # Lower-branch series resonator
        L = getUnitsWithScale(Kl / (delta * Cshunt[-1]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * Cshunt[-1] * delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Wire between components
        x1 = x; x2 = x; y1 = y+90; y2 = y+120
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
    else:
        x1 = x; x2 = x+step; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    

    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# Export Direct Coupled filters with shunt resonators
def get_DirectCoupled_ShuntResonators_QucsSchematic(params):
    # Unpack the dictionary
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    Mask = params['Mask']
    Response = params['Response']
    
    count_L = 0
    count_C = 0
    count_TL = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 200 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -36
    ytext_upper = -64


    syn_params = {}
    syn_params['gi'] = params['gi']
    syn_params['N'] = params['N']
    syn_params['ZS'] = params['ZS']
    syn_params['ZL'] = params['ZL']
    syn_params['f1'] = float(params['f1'])*1e6
    syn_params['f2'] = float(params['f2'])*1e6
    
    DC_Type = 0
    if (params['DC_Type'] == 'C-coupled shunt resonators'):
        syn_params['Xres'] = [float(i)*1e-9 for i in params['Xres']] # Resonator inductance
        Cseries, Lres, Cres = synthesize_DC_Filter_C_Coupled_Shunt_Resonators(syn_params)
        DC_Type = 0
    elif(params['DC_Type'] == 'L-coupled shunt resonators'):
        syn_params['Xres'] = [float(i)*1e-12 for i in params['Xres']]# Resonator capacitance
        Lseries, Lres, Cres = synthesize_DC_Filter_L_Coupled_Shunt_Resonators(syn_params)
        DC_Type = 1
    elif(params['DC_Type'] == 'Quarter-Wave coupled resonators'):
        Z0_TL, len_TL, Lres, Cres = synthesize_DC_Filter_QW_Shunt_Resonators(syn_params)
        len_TL = getUnitsWithScale(len_TL, 'Distance')
        Z0_TL = str(round(Z0_TL)) + " Ohm"
        
        DC_Type = 2


    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame  
    if (N < 4):
        frame_DIN = 3
    elif ((N == 4) or (N <= 6)):
        frame_DIN = 5
    elif(N > 6):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    step = 150
    

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 90) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 120) + " 0 0 0 0>\n"

    # Wires to the filter
    x1 = x; x2 = x; y1 = y+60; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    x1 = x; x2 = x+step-30; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += step
    # First coupling element
    if (DC_Type == 0):
        C = getUnitsWithScale(Cseries[0], 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    elif(DC_Type == 1):
        L = getUnitsWithScale(Lseries[0], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
    elif(DC_Type == 2):
        count_TL += 1
        ytext_upper -= 20
        components += "<TLIN Line" + str(count_TL) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + Z0_TL + "\" 1 \"" + len_TL + "\" 1 \"0 dB\" 0 \"26.85\" 0>\n"

    for i in range (0, N):
            x += step

            # Wire to the resonator
            x1 = x-step+30; x2 = x; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Resonator
            C = getUnitsWithScale(Cres[i], 'Capacitance', 3)
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x-60) + " " + str(y + 90) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x-60) + " " + str(y + 120) + " 0 0 0 0>\n"

            L = getUnitsWithScale(Lres[i], 'Inductance', 3)
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x+60) + " " + str(y + 90) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x+60) + " " + str(y + 120) + " 0 0 0 0>\n"

            # Wires to the resonator
            x1 = x; x2 = x; y1 = y; y2 = y+30
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-60; x2 = x-60; y1 = y+60; y2 = y+30
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y+60; y2 = y+30
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-60; x2 = x; y1 = y+30; y2 = y+30
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x; x2 = x+60; y1 = y+30; y2 = y+30
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
           
            # Next coupling element
            x += step
            if (DC_Type == 0):
                C = getUnitsWithScale(Cseries[i+1], 'Capacitance', 3)
                count_C += 1
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            elif(DC_Type == 1):
                L = getUnitsWithScale(Lseries[i+1], 'Inductance', 3)
                count_L += 1
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
            elif(DC_Type == 2):
                count_TL += 1
                components += "<TLIN Line" + str(count_TL) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + Z0_TL + "\" 1 \"" + len_TL + "\" 1 \"0 dB\" 0 \"26.85\" 0>\n"

            # Wire to the current resonator
            x1 = x-30; x2 = x-step; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 90) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 120) + " 0 0 0 0>\n"

    # Wires to the filter
    x1 = x; x2 = x; y1 = y+60; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    x1 = x; x2 = x-step+30; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# Returns a footer for the schematics containing the title, the simulation block, the equations and the diagrams
def getFooter(params, y_offset):
    f_start = params['f_start']
    f_stop = params['f_stop']
    n_points = params['n_points']
    Response = params['Response']
    N = params['N']
    ZS = params['ZS']
    Mask = params['Mask']
    Ripple = params['Ripple']
    fc = params['fc']

    # S-parameter simulation block
    x_block = 60
    y_block = y_offset
    components = ''
    components += "<.SP SP1 1 " + str(x_block) + " " + str(y_block) + " 0 67 0 0 \"lin\" 1 \"" + str(f_start) + " MHz \" 1 \"" + str(f_stop) + " MHz \" 1 \"" + str(n_points) + "\" 1 \"no\" 0 \"1\" 0 \"2\" 0>\n"
    components += "<Eqn Eqn1 1 " + str(1230) + " " + str(600) + " -28 15 0 0 \"S21_dB=dB(S[2,1])\" 1 \"S11_dB=dB(S[1,1])\" 1 \"S22_dB=dB(S[2,2])\" 1 \"yes\" 0>\n"
    components += "<Eqn Eqn2 1 " + str(1230) + " " + str(780) + " -28 15 0 0 \"gd=groupdelay(S,2,1)\" 1 \"phase=(180/pi)*angle(S[2,1])\" 1 \"yes\" 0>\n"

    # Text
    y_title = str(50)
    paintings = "<Paintings>\n"
    today = date.today()
    copyright = " - Copyright \u00A9 2020-" + str(today.year) + " Andrés Martínez Mera - GNU Public License Version 3"

    paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" 
                    + Response + " " + Mask + " Filter" + ", Order: " + str(N) + ", Ripple: " + str(Ripple) + " dB, "
                    + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")

    
    # Diagrams
    x_size = 400
    y_size = 300
    x_pos = 170
    y_pos = y_offset + 500
    diagrams = "<Diagrams>\n"
    # Response
    paintings += ("<Text " + str(x_pos + round(x_size/2) - 50) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Response\">\n")
    diagrams += ("<Rect " + str(x_pos) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 0 -50 5 5 1 -0.1 0.5 1.1 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"S21_dB\" #ff0000 0 3 0 0 0>\n")
    diagrams += str("<\"S11_dB\" #0000ff 0 3 0 0 0>\n")
    diagrams += "</Rect>\n"
    
    # Group Delay and phase
    paintings += ("<Text " + str(x_pos + x_size + 100 + round(x_size/2) - 120) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Group Delay and Phase\">\n")
    diagrams += ("<Rect " + str(x_pos + x_size + 100 ) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 1 -4 1 4 0 -180 90 180 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"gd\" #0000ff 0 3 0 0 0>\n")
    diagrams += str("<\"phase\" #00aa00 0 3 0 0 1>\n")
    diagrams += "</Rect>\n"

    diagrams += "</Diagrams>\n"
    paintings += "</Paintings>\n"

    footer = diagrams + paintings

    return components, footer