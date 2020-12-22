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

# FORM 1.3 - Calculation of the reflection coefficient and S11 given the SWR
class SWRToReflectionCoefficientForm(forms.Form):
    SWR = forms.FloatField(initial=1.3,  label='SWR')

    def __init__(self, *args, **kwargs):
        super(SWRToReflectionCoefficientForm, self).__init__(*args, **kwargs)
        self.fields['SWR'].widget.attrs['min'] = 1    

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

# FORM 3 - Calculation of the reflection coefficient and S11 given the SWR

class ParallelResistorForm(forms.Form):
    CHOICES = (
        ('0', "4.7"),
        ('1', "10"),
        ('2', "18"),
        ('3', "33"),
        ('4', "47"),
        ('5', "100"),
        ('6', "220"),
        ('7', "330"),
        ('8', "470"),
        ('9', "680"),
        ('10', "1k"),
        ('11', "2k2"),
        ('12', "3k3"),
        ('13', "4k7"),
        ('14', "6k8"),
        ('15', "10k"),
        ('16', "18k"),
        ('17', "22k"),
        ('18', "27k"),
        ('19', "33k"),
        ('20', "68k"),
        ('21', "100k"),
    )

    R1 = forms.CharField(label='R\u2081', max_length=6, initial='1k')
    R2 = forms.CharField(label='R\u2082', max_length=6, initial='3k3')

    def clean_R1(self):
        R1 = self.cleaned_data['R1']
        return R1

    def clean_R2(self):
        R2 = self.cleaned_data['R2']
        return R2