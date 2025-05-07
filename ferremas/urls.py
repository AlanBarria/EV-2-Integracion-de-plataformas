from django.urls import path
from . import views

urlpatterns = [
    path('inicio', views.inicio, name='inicio'),
    path('crud_herramientas/', views.crud_herramientas, name='crud_herramientas'),
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registro, name='registro'),  # Asumiendo que ya tienes login
    path('tarjetas/', views.listar_tarjetas, name='listar_tarjetas'),
    path('pagar/<int:tarjeta_id>/', views.pagar_con_tarjeta, name='pagar_con_tarjeta'),
    

]
