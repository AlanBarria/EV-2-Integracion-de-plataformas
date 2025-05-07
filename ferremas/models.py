from django.db import models

class Herramienta(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    imagen = models.ImageField(upload_to='herramientas/', null=True, blank=True)


class Tarjeta(models.Model):
    numero = models.CharField(max_length=20)
    fecha_expiracion = models.CharField(max_length=5)
    cvv = models.CharField(max_length=4)
    fecha_guardado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tarjeta terminada en {self.numero[-4:]}", self.nombre
