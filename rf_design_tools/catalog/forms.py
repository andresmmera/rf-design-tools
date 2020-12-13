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


# FORM 1.2 - Calculation of the reflection coefficient given the load impedance
class ImpedanceToReflectionCoefficientForm(forms.Form):
    
    ZR = forms.FloatField(initial=73.44,  label='Re{Z}')
    ZI = forms.FloatField(initial=7.92, label='Im{Z}')   
    Z0 = forms.FloatField(initial=50, label='Z\u2080')

    def __init__(self, *args, **kwargs):
        super(ImpedanceToReflectionCoefficientForm, self).__init__(*args, **kwargs)
        self.fields['Z0'].widget.attrs['min'] = 1e-6
        self.fields['ZR'].widget.attrs['min'] = 1e-6

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

