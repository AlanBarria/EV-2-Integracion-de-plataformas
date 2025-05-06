from django.db import models

class Herramienta(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    imagen = models.ImageField(upload_to='herramientas/', null=True, blank=True)

    def __str__(self):
        return self.nombre

