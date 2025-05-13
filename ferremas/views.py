from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm, OrdenForm
from django.http import HttpResponse, JsonResponse
from .models import Herramienta, Orden
from django.contrib import messages
from django.contrib.auth import authenticate, login
from ferremas.webpay import confirmar_transaccion, crear_transaccion
import os

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
