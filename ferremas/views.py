from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm, OrdenForm
from django.http import HttpResponse, JsonResponse
from .models import Herramienta, Orden
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from ferremas.webpay import confirmar_transaccion, crear_transaccion
import os
import requests
from .serializers import HerramientaSerializer, OrdenSerializer
from django.contrib.auth.decorators import login_required

@login_required
def inicio(request):
    categoria = request.GET.get('categoria')
    if categoria:
        herramientas = Herramienta.objects.filter(categoria=categoria)
    else:
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
                usuario.is_superuser = True
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

from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect('iniciar_sesion') 

from django.shortcuts import render, redirect, get_object_or_404
from .models import Herramienta
from .forms import HerramientaForm
from django.conf import settings
from django.contrib.auth.decorators import login_required

@login_required
def crud_herramientas(request):
    herramientas = Herramienta.objects.all()
    form = HerramientaForm()
    editar_id = request.GET.get('editar_id')
    herramienta_editada = None

    # Cargar datos para edición
    if editar_id:
        herramienta_editada = get_object_or_404(Herramienta, id=editar_id)
        form = HerramientaForm(instance=herramienta_editada)

    # Guardar cambios
    if request.method == 'POST':
        editar_id = request.POST.get('editar_id')
        herramienta_editada = None
        if editar_id:
            herramienta_editada = get_object_or_404(Herramienta, id=editar_id)
            form = HerramientaForm(request.POST, request.FILES, instance=herramienta_editada)
        else:
            form = HerramientaForm(request.POST, request.FILES)

        if form.is_valid():
            data = {
            'codigo_interno': form.cleaned_data['codigo_interno'],
            'codigo_fabricante': form.cleaned_data['codigo_fabricante'],
            'marca': form.cleaned_data['marca'],
            'nombre': form.cleaned_data['nombre'],
            'descripcion': form.cleaned_data['descripcion'],
            'categoria': form.cleaned_data['categoria'],  # <-- esta línea es clave
            'precio': str(form.cleaned_data['precio']),
            'stock': str(form.cleaned_data['stock']),
        }

            files = {}
            if 'imagen' in request.FILES:
                files['imagen'] = request.FILES['imagen']

            if editar_id:
                # Editar herramienta existente con PATCH
                if files:
                    response = requests.patch(
                        f'http://127.0.0.1:8000/api/herramientas/{editar_id}/',
                        data=data,
                        files=files
                    )
                else:
                    response = requests.patch(
                        f'http://127.0.0.1:8000/api/herramientas/{editar_id}/',
                        data=data
                    )
                if response.status_code in [200, 202]:
                    messages.success(request, 'Herramienta editada exitosamente.')
                    return redirect('crud_herramientas')
                else:
                    messages.error(request, 'Error al editar herramienta.')
            else:
                # Crear herramienta nueva con POST
                if files:
                    response = requests.post(
                        'http://127.0.0.1:8000/api/herramientas/',
                        data=data,
                        files=files
                    )
                else:
                    response = requests.post(
                        'http://127.0.0.1:8000/api/herramientas/',
                        data=data
                    )
                if response.status_code == 201:
                    messages.success(request, 'Herramienta creada exitosamente.')
                    return redirect('crud_herramientas')
                else:
                    messages.error(request, 'Error al crear herramienta.')

    # Eliminar
    if request.method == 'GET' and 'eliminar_id' in request.GET:
        herramienta = get_object_or_404(Herramienta, id=request.GET['eliminar_id'])
        herramienta.delete()
        messages.success(request, 'Herramienta eliminada correctamente.')
        return redirect('crud_herramientas')

    return render(request, 'ferremas/admin/crud_herramientas.html', {
        'herramientas': herramientas,
        'form': form,
        'editar_id': editar_id,
        'herramienta_editada': herramienta_editada,
    })

import uuid
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

@csrf_exempt
def iniciar_pago(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        request.session['producto_id'] = producto_id  # Guardar en sesión

        orden_id = 'orden123'
        sesion_id = 'session123'
        herramienta = Herramienta.objects.get(id=producto_id)
        monto = int(herramienta.precio)

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
        producto_id = request.session.get('producto_id')
        if producto_id:
            return redirect('resumen_compra', producto_id=producto_id)
        return render(request, 'ferremas/resumen_compra.html', {'resultado': resultado})
    else:
        return render(request, 'ferremas/error.html', {'error': 'Pago no autorizado'})

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
    try:
        amount_str = request.GET.get('amount', '0').replace(',', '.')
        from_currency = request.GET.get('from_currency', 'USD')
        to_currency = request.GET.get('to_currency', 'CLP')

        amount = float(amount_str)

        exchange_rate = 850.0  # Tasa ficticia
        converted_amount = amount * exchange_rate

        return JsonResponse({
            'original_amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': converted_amount,
            'exchange_rate': exchange_rate,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
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

from rest_framework import viewsets

#API creada
class HerramientaViewSet(viewsets.ModelViewSet):
    queryset = Herramienta.objects.all()
    serializer_class = HerramientaSerializer
class OrdenViewSet(viewsets.ModelViewSet):
    queryset = Orden.objects.all()
    serializer_class = OrdenSerializer

#Categorías

def catalogo(request):
    categoria = request.GET.get('categoria')
    if categoria:
        herramientas = Herramienta.objects.filter(categoria=categoria)
    else:
        herramientas = Herramienta.objects.all()

    return render(request, 'ferremas/catalogo.html', {'herramientas': herramientas})



def detalle_herramienta(request, herramienta_id):
    herramienta = get_object_or_404(Herramienta, id=herramienta_id)
    return render(request, 'ferremas/detalle_herramienta.html', {'herramienta': herramienta})

def resumen_compra(request, producto_id):
    herramienta = get_object_or_404(Herramienta, id=producto_id)
    return render(request, 'ferremas/resumen_compra.html', {'herramienta': herramienta})

def pago_exitoso(request):
    token = request.GET.get('token_ws')

    if not token:
        return render(request, 'ferremas/error.html', {'error': 'Token no recibido desde Webpay'})

    # Confirmar con Webpay
    resultado = confirmar_transaccion(token)

    if resultado and resultado.get("status") == "AUTHORIZED":
        producto_id = request.session.get('producto_id')

        if producto_id:
            return redirect('resumen_compra', producto_id=producto_id)
        else:
            return render(request, 'ferremas/error.html', {'error': 'Producto no encontrado en sesión'})
    else:
        return render(request, 'ferremas/error.html', {'error': 'Pago no autorizado'})