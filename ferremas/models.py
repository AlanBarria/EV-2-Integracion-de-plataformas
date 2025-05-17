from django.db import models
from django.contrib.auth.models import User


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



