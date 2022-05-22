# Get units with scale, etc.
from ..utilities import *
from datetime import date



# This function exports the filter as a Qucs schematic
def getPiAttenuatorQucsSchematic(params):
    # Unpack the dictionary
    Structure = params['Structure']
    att =  params['att']
    ZS = params['ZS']
    ZL = params['ZL']
    f0 = params['f0']
    Pin = params['Pin']


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

    # Frame
    datasetName = "sample.dat"
    title = Structure + " Attenuator (" + str(att) + " dB)"
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

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
    paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" + Structure + " Attenuator (" + str(att) + " dB"+ "\">\n")

    

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