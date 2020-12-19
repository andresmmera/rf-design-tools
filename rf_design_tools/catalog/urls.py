from django.urls import path
from catalog import views
from catalog.views import *

urlpatterns = [
    path('', tools_catalog, name='tools-catalog'),
    
    path('tool/reflection_coefficient', CalculateReflectionCoefficientView, name='reflection-coeff'),
    path('tool/reflection_coefficient/docs', ReflectionCoefficientDocs, name='reflection-coeff-docs'),
    
    path('tool/rf_power_converter', CalculatePowerConverterView, name='rf_power_converter'),
    path('tool/rf_power_converter/docs', ReflectionCoefficientDocs, name='rf_power_converter-docs'),
]