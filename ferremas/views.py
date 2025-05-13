from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm, OrdenForm
from django.http import HttpResponse, JsonResponse
from .models import Herramienta, Orden
from django.contrib import messages
from django.contrib.auth import authenticate, login
from ferremas.webpay import confirmar_transaccion, crear_transaccion
import os
import requests

def inicio(request):
    herramientas = Herramienta.objects.all()
    return render(request, 'ferremas/inicio.html', {'herramientas': herramientas})

def admin_vista(request):
    return render(request, 'ferremas/admin_vista.html')

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)  # No guardar aún en la base de datos
            if usuario.email.endswith('@admin.cl'):
                usuario.is_staff = True
                usuario.is_superusuer = True
            usuario.save()  # Ahora sí lo guardamos con is_staff si corresponde
            return redirect('iniciar_sesion')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'ferremas/registro.html', {'form': form})


def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            # Redirección según si es staff o no
            if usuario.is_staff:
                return redirect('crud_herramientas')  # Ruta para personal administrativo
            else:
                return redirect('inicio')  # Ruta para usuario común
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    return render(request, 'ferremas/login.html')



from django.shortcuts import render, redirect, get_object_or_404
from .models import Herramienta
from .forms import HerramientaForm
from django.conf import settings

def crud_herramientas(request):
    herramientas = Herramienta.objects.all()
    form = HerramientaForm()

    # Crear o editar
    if request.method == 'POST':
        if 'editar_id' in request.POST:
            herramienta = get_object_or_404(Herramienta, id=request.POST['editar_id'])
            form = HerramientaForm(request.POST, request.FILES, instance=herramienta)
        else:
            form = HerramientaForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('crud_herramientas')

    # Eliminar
    elif request.method == 'GET' and 'eliminar_id' in request.GET:
        herramienta = get_object_or_404(Herramienta, id=request.GET['eliminar_id'])
        herramienta.delete()
        return redirect('crud_herramientas')

    # Cargar datos para edición
    elif request.method == 'GET' and 'editar_id' in request.GET:
        herramienta = get_object_or_404(Herramienta, id=request.GET['editar_id'])
        form = HerramientaForm(instance=herramienta)

    return render(request, 'ferremas/admin/crud_herramientas.html', {
        'herramientas': herramientas,
        'form': form
    })

import uuid
def iniciar_pago(request):
    if request.method == 'POST':
        orden_id = 'orden123'
        sesion_id = 'session123'
        monto = 1000

        respuesta = crear_transaccion(orden_id, sesion_id, monto)

        if respuesta and 'token' in respuesta and 'url' in respuesta:
            return redirect(f"{respuesta['url']}?token_ws={respuesta['token']}")
        else:
            return render(request, 'ferremas/error.html', {'error': 'No se pudo iniciar la transacción'})
    return render(request, 'pago.html')


def confirmar_pago(request):
    token = request.GET.get('token_ws')
    if not token:
        return render(request, 'ferremas/error.html', {'error': 'Token no recibido'})

    resultado = confirmar_transaccion(token)

    if resultado and resultado.get('status') == 'AUTHORIZED':
        return render(request, 'ferremas/pago_exitoso.html', {'resultado': resultado})
    else:
        return render(request, 'ferremas/error.html', {'error': 'Pago no autorizado o fallido', 'detalle': resultado})

#API Banco Central De Chile
# Obtener datos de una serie
def get_series_data(request):
    user = settings.BCCH_USER
    password = settings.BCCH_PASS
    timeseries = request.GET.get('timeseries', 'F022.TPM.TIN.D001.NO.Z.D')
    firstdate = request.GET.get('firstdate', '')
    lastdate = request.GET.get('lastdate', '')

    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?"
        f"user={user}&pass={password}&function=GetSeries&timeseries={timeseries}"
    )
    if firstdate:
        url += f"&firstdate={firstdate}"
    if lastdate:
        url += f"&lastdate={lastdate}"

    response = requests.get(url)
    return JsonResponse(response.json() if response.ok else {'error': 'Error al consultar la serie'}, status=response.status_code)


# Buscar catálogo de series por frecuencia
def search_series(request):
    user = settings.BCCH_USER
    password = settings.BCCH_PASS
    frequency = request.GET.get('frequency', 'DAILY')

    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?"
        f"user={user}&pass={password}&function=SearchSeries&frequency={frequency}"
    )

    response = requests.get(url)
    return JsonResponse(response.json() if response.ok else {'error': 'Error al consultar el catálogo'}, status=response.status_code)

def convert_currency(request):
    amount = float(request.GET.get('amount', 0))  # Monto a convertir
    from_currency = request.GET.get('from_currency', 'USD')  # Moneda de origen
    to_currency = request.GET.get('to_currency', 'CLP')  # Moneda de destino
    
    # Aquí deberías obtener las tasas de cambio de una API o base de datos
    exchange_rate = 850.0  # Este es un valor ficticio para ejemplo

    converted_amount = amount * exchange_rate
    response_data = {
        'original_amount': amount,
        'from_currency': from_currency,
        'to_currency': to_currency,
        'converted_amount': converted_amount,
        'exchange_rate': exchange_rate,
    }

    return JsonResponse(response_data)


def get_exchange_rate():
    # Aquí haces la solicitud a la API del Banco Central para obtener la tasa de cambio
    # Supongamos que la tasa de cambio de USD a CLP es lo que necesitas.
    user = settings.BCCH_USER
    password = settings.BCCH_PASS
    timeseries = 'F022.TPM.TIN.D001.NO.Z.D'  # Código de la serie para la tasa de cambio

    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?"
        f"user={user}&pass={password}&function=GetSeries&timeseries={timeseries}"
    )

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "Series" in data:
            # Supongamos que la última tasa es la que nos interesa
            last_observation = data['Series']['Obs'][-1]
            exchange_rate = float(last_observation['value'])  # La tasa de cambio
            return exchange_rate
    return 850.0  # Valor por defecto si no se obtiene respuesta

def update_cart_total(request):
    # Obtener los artículos en el carrito (esto depende de cómo esté configurado tu carrito)
    cart_items = get_cart_items()  # Esta función debe devolver los productos en el carrito
    total_usd = sum(item.price for item in cart_items)

    # Obtener la tasa de cambio actual desde la API del Banco Central
    exchange_rate = get_exchange_rate()

    # Calcular el total en CLP (o la moneda de destino)
    total_clp = total_usd * exchange_rate

    response_data = {
        'total_usd': total_usd,
        'total_clp': total_clp,
        'exchange_rate': exchange_rate,
    }

    return JsonResponse(response_data)