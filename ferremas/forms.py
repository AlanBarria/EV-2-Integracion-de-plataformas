from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Herramienta

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class HerramientaForm(forms.ModelForm):
    class Meta:
        model = Herramienta
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'imagen']