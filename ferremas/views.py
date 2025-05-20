from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets
import requests
import uuid
from .models import Carrito, ItemCarrito, Herramienta
from decimal import Decimal
from .forms import RegistroUsuarioForm, OrdenForm, HerramientaForm
from .models import Herramienta, Orden
from .serializers import HerramientaSerializer, OrdenSerializer
from ferremas.webpay import confirmar_transaccion, crear_transaccion
from django.views.decorators.cache import never_cache
from .models import MensajeContacto
from .forms import MensajeContactoForm

@login_required
def enviar_mensaje(request):
    if request.method == 'POST':
        form = MensajeContactoForm(request.POST)
        if form.is_valid():
            MensajeContacto.objects.create(
                usuario=request.user,
                mensaje=form.cleaned_data['mensaje']
            )
            return redirect('inicio')
    else:
        form = MensajeContactoForm()

    return render(request, 'ferremas/enviar_mensaje.html', {'form': form})

@login_required
def ver_mensajes(request):
    mensajes = MensajeContacto.objects.all().order_by('-fecha_envio')
    return render(request, 'ferremas/ver_mensajes.html', {'mensajes': mensajes})


@never_cache
@login_required
def inicio(request):
    categoria = request.GET.get('categoria')
    if categoria:
        herramientas = Herramienta.objects.filter(categoria=categoria)
    else:
        herramientas = Herramienta.objects.all()

    return render(request, 'ferremas/inicio.html', {'herramientas': herramientas})

def admin_vista(request):
    return render(request, 'ferremas/ver_mensajes.html')

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            if usuario.email.endswith('@admin.cl'):
                usuario.is_staff = True
                usuario.is_superuser = True
            usuario.save()
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
            # Revisar dominio del email para redireccionar
            if usuario.email.endswith('@bodega.cl'):
                return redirect('almacen')  # Cambia 'almacen' por el nombre de la url correcta
            elif usuario.email.endswith('@contador.cl'):
                return redirect('compras_usuarios')  # Cambia 'compras_usuarios' por la url correcta
            elif usuario.is_staff:
                return redirect('crud_herramientas')
            else:
                return redirect('inicio')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    return render(request, 'ferremas/login.html')


def logout_view(request):
    logout(request)
    return redirect('iniciar_sesion')

@login_required
def crud_herramientas(request):
    herramientas = Herramienta.objects.all()
    form = HerramientaForm()
    editar_id = request.GET.get('editar_id')
    herramienta_editada = None

    if editar_id:
        herramienta_editada = get_object_or_404(Herramienta, id=editar_id)
        form = HerramientaForm(instance=herramienta_editada)

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
                'categoria': form.cleaned_data['categoria'],
                'precio': str(form.cleaned_data['precio']),
                'stock': str(form.cleaned_data['stock']),
            }

            files = {}
            if 'imagen' in request.FILES:
                files['imagen'] = request.FILES['imagen']

            if editar_id:
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

@csrf_exempt
def iniciar_pago(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')

        if producto_id:
            # Compra directa de un producto individual
            try:
                producto = Herramienta.objects.get(id=producto_id)
                cantidad = int(request.POST.get('cantidad', 1))
                total = producto.precio * cantidad
            except Herramienta.DoesNotExist:
                return render(request, 'ferremas/error.html', {'error': 'Producto no encontrado.'})
        else:
            #Compra desde el carrito
            try:
                carrito = Carrito.objects.get(usuario=request.user)
                items = ItemCarrito.objects.filter(carrito=carrito)

                if not items.exists():
                    return render(request, 'ferremas/error.html', {'error': 'El carrito está vacío.'})
                
                total = sum(item.herramienta.precio * item.cantidad for item in items)

            except Carrito.DoesNotExist:
                return render(request, 'ferremas/error.html', {'error': 'El carrito está vacío.'})

            
        orden_id = str(uuid.uuid4())[:12]
        sesion_id = str(uuid.uuid4())[:12]

        respuesta = crear_transaccion(orden_id, sesion_id, total)

        if respuesta and 'token' in respuesta and 'url' in respuesta:
            return redirect(f"{respuesta['url']}?token_ws={respuesta['token']}")
        else:
            return render(request, 'ferremas/error.html', {'error': 'No se pudo iniciar la transacción'})

    return redirect('ver_carrito')

@csrf_exempt
def confirmar_pago(request):
    token = request.GET.get('token_ws')

    if not token:
        return render(request, 'ferremas/error.html', {'error': 'Token no proporcionado'})

    resultado = confirmar_transaccion(token)

    if resultado and resultado.get('status') == 'AUTHORIZED':
        return render(request, 'ferremas/resumen_compra.html', {'detalle': resultado})
    else:
        return render(request, 'ferremas/error.html', {'error': 'Pago no autorizado o fallido'})
    
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

        exchange_rate = 850.0
        converted_amount = amount * exchange_rate

        if from_currency == 'USD' and to_currency == 'CLP':
            converted_amount = amount * exchange_rate
        elif from_currency == 'CLP' and to_currency == 'USD':
            converted_amount = amount / exchange_rate
        elif from_currency == to_currency:
            converted_amount = amount
        else:
            return JsonResponse({'error': 'Conversión no soportada'}, status=400)

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
    user = settings.BCCH_USER
    password = settings.BCCH_PASS
    timeseries = 'F022.TPM.TIN.D001.NO.Z.D'

    url = (
        f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?"
        f"user={user}&pass={password}&function=GetSeries&timeseries={timeseries}"
    )

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "Series" in data:
            last_observation = data['Series']['Obs'][-1]
            exchange_rate = float(last_observation['value'])
            return exchange_rate
    return 850.0

@login_required
@require_GET
def update_cart_total(request):
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        cart_items = ItemCarrito.objects.filter(carrito=carrito)
    except Carrito.DoesNotExist:
        cart_items = []

    total_clp = sum(item.herramienta.precio * item.cantidad for item in cart_items)
    
    exchange_rate = Decimal(str(get_exchange_rate()))  # Convertir a Decimal para evitar error
    total_usd = total_clp * exchange_rate

    response_data = {
        'total_usd': float(total_usd),  # opcional: convertir a float para JSON
        'total_clp': float(total_clp),
        'exchange_rate': float(exchange_rate),
    }

    return JsonResponse(response_data)


class HerramientaViewSet(viewsets.ModelViewSet):
    queryset = Herramienta.objects.all()
    serializer_class = HerramientaSerializer

class OrdenViewSet(viewsets.ModelViewSet):
    queryset = Orden.objects.all()
    serializer_class = OrdenSerializer

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


@login_required
@require_GET
def pago_exitoso(request):
    token = request.GET.get('token_ws')

    if not token:
        return render(request, 'ferremas/error.html', {'error': 'Token no recibido desde Webpay'})

    resultado = confirmar_transaccion(token)

    if resultado and resultado.get("status") == "AUTHORIZED":
        carrito = request.session.get('carrito', {})
        herramientas = []

        for item_id, datos in carrito.items():
            try:
                herramienta = Herramienta.objects.get(id=int(item_id))
                herramientas.append({
                    'nombre': herramienta.nombre,
                    'imagen': herramienta.imagen,
                    'categoria': herramienta.get_categoria_display(),
                    'descripcion': herramienta.descripcion,
                    'precio': herramienta.precio,
                    'cantidad': datos['cantidad'],
                    'subtotal': herramienta.precio * datos['cantidad']
                })
            except Herramienta.DoesNotExist:
                continue

        total = sum(item['subtotal'] for item in herramientas)

        # Guardar en sesión para la vista resumen
        request.session['resumen_compra'] = {
            'herramientas': herramientas,
            'total': total
        }

        print("RESUMEN GUARDADO:", request.session['resumen_compra'])  # DEBUG

        request.session['carrito'] = {}
        request.session.modified = True
        request.session.save()  # <- fuerza el guardado

        return render(request, 'resumen_compra')

    return render(request, 'ferremas/error.html', {'error': 'Pago no autorizado'})


def resumen_compra(request):
    if 'resumen_compra' not in request.session:
        return redirect('inicio')

    resumen = request.session['resumen_compra']
    herramientas = resumen.get('herramientas', [])
    total = resumen.get('total', 0)

    return render(request, 'ferremas/resumen_compra.html', {
        'herramientas': herramientas,
        'total': total
    })

@require_POST
def agregar_al_carrito(request, herramienta_id):
    cantidad = int(request.POST.get('cantidad', 1))
    herramienta = get_object_or_404(Herramienta, pk=herramienta_id)

    # Obtener o crear el carrito del usuario
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)

    # Buscar si ya existe el item en el carrito
    item, creado_item = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        herramienta=herramienta,
        defaults={'cantidad': cantidad}
    )

    # Si ya existía, sumar la cantidad
    if not creado_item:
        item.cantidad += cantidad
        item.save()

    return redirect('ver_carrito')


@login_required
def ver_carrito(request):
    try:
        carrito = Carrito.objects.get(usuario=request.user)
        items_bd = ItemCarrito.objects.filter(carrito=carrito)
    except Carrito.DoesNotExist:
        items_bd = []

    items = []
    total = 0

    for item in items_bd:
        herramienta = item.herramienta
        cantidad = item.cantidad
        precio = herramienta.precio
        subtotal = precio * cantidad

        items.append({
            'herramienta_id': herramienta.id,
            'nombre': herramienta.nombre,
            'monto': precio,
            'cantidad': cantidad,
            'total': subtotal
        })

        total += subtotal

    return render(request, 'ferremas/carrito.html', {
        'items': items,
        'total_carrito': total
    })

@require_POST
@login_required
def actualizar_cantidad(request, herramienta_id):
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        carrito = get_object_or_404(Carrito, usuario=request.user)
        item = get_object_or_404(ItemCarrito, carrito=carrito, herramienta_id=herramienta_id)
        item.cantidad = cantidad
        item.save()
        return redirect('ver_carrito')

@require_POST
@login_required
def eliminar_del_carrito(request, herramienta_id):
    carrito = get_object_or_404(Carrito, usuario=request.user)
    item = get_object_or_404(ItemCarrito, carrito=carrito, herramienta_id=herramienta_id)
    item.delete()
    return redirect('ver_carrito')

# ferremas/views.py

from django.shortcuts import render, redirect
from .models import Herramienta
from .forms import HerramientaStockForm

def almacen(request):
    herramientas = Herramienta.objects.all()

    if request.method == 'POST':
        for herramienta in herramientas:
            stock_field = f'stock_{herramienta.id}'
            if stock_field in request.POST:
                nuevo_stock = request.POST.get(stock_field)
                if nuevo_stock.isdigit():
                    herramienta.stock = int(nuevo_stock)
                    herramienta.save()
        return redirect('almacen')  # Redirige a sí misma tras actualizar

    return render(request, 'ferremas/almacen.html', {'herramientas': herramientas})

@login_required
def compras_usuarios(request):
    ordenes = Orden.objects.all().prefetch_related('detalles', 'cliente')
    total_general = sum(orden.monto for orden in ordenes)

    return render(request, 'ferremas/compras_usuarios.html', {
        'ordenes': ordenes,
        'total_general': total_general
    })


