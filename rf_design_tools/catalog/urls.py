from django.urls import path
from catalog import views

urlpatterns = [
    path('', views.ToolListView.as_view(), name='tools'),
    path('tool/reflection_coefficient', views.CalculateReflectionCoefficientView, name='reflection-coeff'),
    path('tool/rf_power_converter', views.CalculatePowerConverterView, name='rf_power_converter'),
]