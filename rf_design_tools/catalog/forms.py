from django import forms
from django.core.exceptions import ValidationError

# FORM 1.1 - Calculation of the load impedance given the reflection coefficient

class ReflectionCoefficientToImpedanceForm(forms.Form):
    
    gamma_mag = forms.FloatField(initial=0.2, label='|\u0393|')
    gamma_ang = forms.FloatField(initial=15, label='\u2220 \u0393 (\u00B0)')   
    Z0 = forms.FloatField(initial=50, label='Z\u2080')

    def __init__(self, *args, **kwargs):
        super(ReflectionCoefficientToImpedanceForm, self).__init__(*args, **kwargs)
        self.fields['Z0'].widget.attrs['min'] = 1e-6
        self.fields['gamma_mag'].widget.attrs['min'] = 1e-6
        self.fields['gamma_mag'].widget.attrs['max'] = 1

        # Set the width of the boxes
        box_width = 5
        self.fields['gamma_mag'].widget.attrs['style'] = "width:75px"
        self.fields['gamma_ang'].widget.attrs['style'] = "width:75px"
        self.fields['Z0'].widget.attrs['style'] = "width:75px"



# FORM 1.2 - Calculation of the reflection coefficient given the load impedance
class ImpedanceToReflectionCoefficientForm(forms.Form):
    
    ZR = forms.FloatField(initial=73.44,  label='Re{Z}')
    ZI = forms.FloatField(initial=7.92, label='Im{Z}')   
    Z0 = forms.FloatField(initial=50, label='Z\u2080')

    def __init__(self, *args, **kwargs):
        super(ImpedanceToReflectionCoefficientForm, self).__init__(*args, **kwargs)
        self.fields['Z0'].widget.attrs['min'] = 1e-6
        self.fields['ZR'].widget.attrs['min'] = 1e-6

        # Set the width of the boxes
        box_width = 5
        self.fields['ZR'].widget.attrs['style'] = "width:75px"
        self.fields['ZI'].widget.attrs['style'] = "width:75px"
        self.fields['Z0'].widget.attrs['style'] = "width:75px"

# FORM 1.3 - Calculation of the reflection coefficient and S11 given the SWR
class SWRToReflectionCoefficientForm(forms.Form):
    SWR = forms.FloatField(initial=1.3,  label='SWR')

    def __init__(self, *args, **kwargs):
        super(SWRToReflectionCoefficientForm, self).__init__(*args, **kwargs)
        self.fields['SWR'].widget.attrs['min'] = 1
        
        # Set the width of the boxes
        box_width = 5
        self.fields['SWR'].widget.attrs['style'] = "width:75px"

# FORM 2 - RF POWER CONVERTER
class RF_PowerConversionForm(forms.Form):
    
    P = forms.FloatField(initial=0,  label='Power')
    CHOICES_Units = (
        ('0', "W"),
        ('1', "dBm"),
        ('2', "dB\u00B5V (Z\u2080 = 75 \u03A9)"),
        ('3', "dBmV (Z\u2080 = 75 \u03A9)"),
        ('4', "dB\u00B5V (Z\u2080 = 50 \u03A9)"),
        ('5', "dBmV (Z\u2080 = 50 \u03A9)"),
        ('6', "dBpW"),
    )
    old_units = forms.ChoiceField(choices=CHOICES_Units, label='Units', initial='1')
    new_units = forms.ChoiceField(choices=CHOICES_Units, label='New units', initial='2')

    
    
    def clean(self):
        data = self.cleaned_data

        # Check that the power is not negative
        if (data['old_units'] == '0') and (data['P'] <= 0):
            raise ValidationError("P must be > 0")

        return data

    def __init__(self, *args, **kwargs):
        super(RF_PowerConversionForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        box_width = 5
        self.fields['P'].widget.attrs['style'] = "width:75px"


# FORM 3 - Equivalent resistance of two parallel resistors

class ParallelResistorForm(forms.Form):

    R1 = forms.CharField(label='R\u2081', max_length=6, initial='1k')
    R2 = forms.CharField(label='R\u2082', max_length=6, initial='3k3')

    def clean_R1(self):
        R1 = self.cleaned_data['R1']
        return R1

    def clean_R2(self):
        R2 = self.cleaned_data['R2']
        return R2

    def __init__(self, *args, **kwargs):
        super(ParallelResistorForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        box_width = 5
        self.fields['R1'].widget.attrs['style'] = "width:75px"
        self.fields['R2'].widget.attrs['style'] = "width:75px"

# FORM 4 - Equivalent capacitance of two series capacitors

class SeriesCapacitorForm(forms.Form):

    C1 = forms.CharField(label='C\u2081', max_length=6, initial='10p')
    C2 = forms.CharField(label='C\u2082', max_length=6, initial='1p')

    def clean_C1(self):
        C1 = self.cleaned_data['C1']
        return C1

    def clean_C2(self):
        C2 = self.cleaned_data['C2']
        return C2
    
    def __init__(self, *args, **kwargs):
        super(SeriesCapacitorForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        box_width = 5
        self.fields['C1'].widget.attrs['style'] = "width:75px"
        self.fields['C2'].widget.attrs['style'] = "width:75px"


# FORM 5 - Calculate bandwidth in octaves

class BandwidthOctavesForm(forms.Form):

    f1 = forms.FloatField(initial=54,  label='f\u2081 (MHz)')
    f2 = forms.FloatField(initial=1006,  label='f\u2082 (MHz)')

    def __init__(self, *args, **kwargs):
        super(BandwidthOctavesForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        box_width = 5
        self.fields['f1'].widget.attrs['style'] = "width:75px"
        self.fields['f2'].widget.attrs['style'] = "width:75px"

        self.fields['f1'].widget.attrs['min'] = 0.1
        self.fields['f2'].widget.attrs['min'] = 0.1

# FORM 6 - IPn and noisefloor diagram

class IPn_NF_diagramForm(forms.Form):
    # Amplifier parameters
    G = forms.FloatField(initial=16,  label='G (dB)')
    Pout = forms.FloatField(initial=20,  label='Pcarrier (dBm)')
    Delta = forms.FloatField(initial=40,  label='\u0394 (dB)')
    n = forms.IntegerField(initial=3,  label='IM\u2099')

    # Compression and minimum S/I required
    CPo = forms.FloatField(initial=22,  label='P1dB (dBm)')
    SImin = forms.FloatField(initial=35,  label='S/I (dB)')

    # Noise figure
    NF = forms.FloatField(initial=2,  label='NF (dB)')
    BW = forms.FloatField(initial=1200,  label='BW (MHz)')
    T = forms.FloatField(initial=290,  label='T (K)')


    def __init__(self, *args, **kwargs):
        super(IPn_NF_diagramForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        box_width = 5
        self.fields['G'].widget.attrs['style'] = "width:75px"
        self.fields['Pout'].widget.attrs['style'] = "width:75px"
        self.fields['Delta'].widget.attrs['style'] = "width:75px"
        self.fields['n'].widget.attrs['style'] = "width:75px"
        self.fields['CPo'].widget.attrs['style'] = "width:75px"
        self.fields['SImin'].widget.attrs['style'] = "width:75px"
        self.fields['NF'].widget.attrs['style'] = "width:75px"
        self.fields['BW'].widget.attrs['style'] = "width:75px"
        self.fields['T'].widget.attrs['style'] = "width:75px"

        # Set the minimum values
        self.fields['Delta'].widget.attrs['min'] = 10
        self.fields['n'].widget.attrs['min'] = 2
        self.fields['NF'].widget.attrs['min'] = 0.1
        self.fields['BW'].widget.attrs['min'] = 0.1 # 100 kHz
        self.fields['T'].widget.attrs['min'] = 0.1
