from django.db import models

class Herramienta(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    imagen = models.ImageField(upload_to='herramientas/', null=True, blank=True)

class Orden(models.Model):
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



