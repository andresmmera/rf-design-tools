from django import forms
from django.core.exceptions import ValidationError

# FORM 1 - Calculation of the load impedance given the reflection coefficient

class ReflectionCoefficientToImpedanceForm(forms.Form):
    
    gamma_mag = forms.FloatField(initial=0.2, label='|\u0393|')
    gamma_ang = forms.FloatField(initial=15, label='\u2220 \u0393 (\u00B0)')   
    Z0 = forms.FloatField(initial=50, label='Z\u2080')

    def __init__(self, *args, **kwargs):
        super(ReflectionCoefficientToImpedanceForm, self).__init__(*args, **kwargs)
        self.fields['Z0'].widget.attrs['min'] = 1e-6
        self.fields['gamma_mag'].widget.attrs['min'] = 1e-6
        self.fields['gamma_mag'].widget.attrs['max'] = 1


# FORM 2 - Calculation of the reflection coefficient given the load impedance
class ImpedanceToReflectionCoefficientForm(forms.Form):
    
    ZR = forms.FloatField(initial=30,  label='Re{Z}')
    ZI = forms.FloatField(initial=15, label='Im{Z}')   
    Z0 = forms.FloatField(initial=50, label='Z\u2080')

    def __init__(self, *args, **kwargs):
        super(ImpedanceToReflectionCoefficientForm, self).__init__(*args, **kwargs)
        self.fields['Z0'].widget.attrs['min'] = 1e-6
        self.fields['ZR'].widget.attrs['min'] = 1e-6