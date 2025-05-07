from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm,TarjetaForm
from django.http import HttpResponse
from .models import Herramienta,Tarjeta
from django.contrib import messages
from django.contrib.auth import authenticate, login
from transbank.transaccion_completa.transaction import Transaction
from .transbank_config import *

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

def iniciar_transaccion(request):
    # Simula el ingreso manual de datos
    buy_order = "orden12345"
    session_id = "session123"
    amount = 10000
    card_number = "4051885600446623"
    cvv = "123"
    card_expiration_date = "23/12"

    # Guardar la tarjeta (modo pruebas)
    Tarjeta.objects.create(
        numero=card_number,
        fecha_expiracion=card_expiration_date,
        cvv=cvv
    )

    response = Transaction.create(
        buy_order, session_id, amount,
        card_number, cvv, card_expiration_date
    )

    if response['status'] == 'AUTHORIZED':
        return render(request, 'transaccion_exitosa.html', {'response': response})
    else:
        return render(request, 'transaccion_fallida.html', {'response': response})


def listar_tarjetas(request):
    tarjetas = Tarjeta.objects.all()
    editar_id = request.GET.get('editar')
    eliminar_id = request.GET.get('eliminar')
    form = TarjetaForm()

    if editar_id:
        tarjeta_obj = get_object_or_404(Tarjeta, id=editar_id)
        form = TarjetaForm(instance=tarjeta_obj)

    if request.method == 'POST':
        if eliminar_id:
            tarjeta_obj = get_object_or_404(Tarjeta, id=eliminar_id)
            tarjeta_obj.delete()
            return redirect('listar_tarjetas')

        if editar_id:
            tarjeta_obj = get_object_or_404(Tarjeta, id=editar_id)
            form = TarjetaForm(request.POST, instance=tarjeta_obj)
        else:
            form = TarjetaForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar_tarjetas')

    eliminar = None
    if eliminar_id:
        eliminar = get_object_or_404(Tarjeta, id=eliminar_id)

    return render(request, 'tarjetas.html', {
        'tarjetas': tarjetas,
        'form': form,
        'eliminar': eliminar
    })

def pagar_con_tarjeta(request, tarjeta_id):
    tarjeta = get_object_or_404(Tarjeta, id=tarjeta_id)
    buy_order = f"orden-{tarjeta.id}"
    session_id = f"session-{tarjeta.id}"
    amount = 10000

    response = Transaction.create(
        buy_order,
        session_id,
        amount,
        tarjeta.numero,
        tarjeta.cvv,
        tarjeta.fecha_expiracion
    )

    if response['status'] == 'AUTHORIZED':
        return render(request, 'transaccion_exitosa.html', {'response': response})
    else:
        return render(request, 'transaccion_fallida.html', {'response': response})


