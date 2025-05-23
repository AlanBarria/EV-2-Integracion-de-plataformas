# Generated by Django 5.0.6 on 2025-05-19 22:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ferremas', '0008_carrito_itemcarrito'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemOrden',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField()),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('herramienta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ferremas.herramienta')),
                ('orden', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='ferremas.orden')),
            ],
        ),
    ]
