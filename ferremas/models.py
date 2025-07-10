from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User

class MensajeContacto(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Mensaje de {self.usuario.username}"

class RespuestaMensaje(models.Model):
    mensaje_original = models.ForeignKey(MensajeContacto, on_delete=models.CASCADE, related_name='respuestas')
    administrador = models.ForeignKey(User, on_delete=models.CASCADE)
    respuesta = models.TextField()
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Respuesta a {self.mensaje_original.usuario.username}"

class Herramienta(models.Model):
    CATEGORIAS = [
        ('electricas', 'Eléctricas'),
        ('manuales', 'Manuales'),
        ('medicion', 'Medición'),
        ('otros', 'Otros'),
    ]
    codigo_interno = models.CharField(max_length=50)
    codigo_fabricante = models.CharField(max_length=50, null=True, blank=True)
    marca = models.CharField(max_length=50, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    imagen = models.ImageField(upload_to='herramientas/', null=True, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='otros')

    def __str__(self):
        return f"{self.nombre} ({self.codigo_interno})"


class Orden(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Cliente", null=True, blank=True)
    orden_id = models.CharField("ID de la Orden", max_length=100, unique=True)
    sesion_id = models.CharField("ID de Sesión", max_length=100)
    monto = models.PositiveIntegerField("Monto Total")
    estado = models.CharField(
        "Estado del Pago",
        max_length=20,
        choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado'), ('fallido', 'Fallido')],
        default='pendiente'
    )
    fecha_creacion = models.DateTimeField("Fecha de Creación", auto_now_add=True)

    def __str__(self):
        return f"Orden {self.orden_id} - {self.get_estado_display()}"
    
class DetalleOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles')
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad} x {self.herramienta.nombre} en Orden {self.orden.orden_id}"


class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Carrito de {self.usuario.username if self.usuario else 'Usuario anónimo'}"

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    herramienta = models.ForeignKey(Herramienta, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.herramienta.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.herramienta.nombre}"
    
