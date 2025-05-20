from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import pago_exitoso, resumen_compra

urlpatterns = [
    path('inicio', views.inicio, name='inicio'),
    path('crud_herramientas/', views.crud_herramientas, name='crud_herramientas'),
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registro, name='registro'),  # Asumiendo que ya tienes login
    path('webpay/iniciar/', views.iniciar_pago, name='iniciar_pago'),
    path('webpay/confirmar/', views.confirmar_pago, name='confirmar_pago'),
    path('serie/', views.get_series_data, name='get_series_data'),
    path('catalogo/', views.search_series, name='search_series'),
    path('api/convert/', views.convert_currency, name='convert_currency'),
    path('api/logout/', views.logout_view, name='logout'),  
    path('catalogo/', views.catalogo, name='catalogo'),
    path('herramienta/<int:herramienta_id>/', views.detalle_herramienta, name='detalle_herramienta'),
    path('pago-exitoso/', pago_exitoso, name='pago_exitoso'),
    path('resumen-compra/', resumen_compra, name='resumen_compra'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:herramienta_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:herramienta_id>/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/eliminar/<int:herramienta_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('almacen/', views.almacen, name='almacen'),
    path('compras/', views.compras_usuarios, name='compras_usuarios'),

]
