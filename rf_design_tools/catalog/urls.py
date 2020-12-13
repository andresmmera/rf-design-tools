from django.urls import path
from catalog import views

urlpatterns = [
    path('', views.ToolListView.as_view(), name='tools'),
    path('tool/reflection_coefficient', views.CalculateReflectionCoefficientForm, name='reflection-coeff'),
]