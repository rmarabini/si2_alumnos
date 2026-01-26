# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# author: rmarabini
"""Modelos de la aplicación de pago """
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.core.validators import MinLengthValidator


class CodigoRespuesta(models.TextChoices):
    """Enum para los códigos de respuesta"""
    RESPUESTA_OK = '000', 'Respuesta OK'
    RESPUESTA_ERR = 'ERR', 'Error'
    # Agrega más opciones aquí si es necesario


class Tarjeta(models.Model):
    """Definición del modelo para representar una tarjeta de credito"""
    numero = models.CharField(max_length=19, primary_key=True)
    nombre = models.CharField(max_length=128)
    fechaCaducidad = models.CharField(max_length=5)
    codigoAutorizacion = models.CharField(max_length=3)

    def __str__(self):
        return f"{self.nombre} (Numero: {self.numero})"

    class Meta:
        db_table = 'tarjeta'


class Pago(models.Model):
    """Definición del modelo para registrar un pago"""
    # use min_lentgh=1 to avoid empty strings
    # since "" is a valid string in Python
    idComercio = models.CharField(max_length=16)
    idTransaccion = models.CharField(max_length=16)
    importe = models.FloatField()
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.CASCADE)
    marcaTiempo = models.DateTimeField(auto_now=True)
    codigoRespuesta = models.CharField(max_length=3,
                                       default=CodigoRespuesta.RESPUESTA_OK)

    class Meta:
        # Garantiza que cada persona solo pueda emitir un pago con el mismo IdTransacción en el mismo comercio
        constraints = [UniqueConstraint(fields=['idTransaccion',
                                                'idComercio'],
                                        name='unique_blocking_pago')]
        db_table = 'pago'

    def __str__(self):
        return "Pago para " + f"{self.idComercio} con importe " + f"{self.importe}"
