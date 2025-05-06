from django.shortcuts import render, redirect
from .forms import RegistroUsuarioForm
from django.http import HttpResponse
from .models import Herramienta
from django.contrib import messages
from django.contrib.auth import authenticate, login

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
