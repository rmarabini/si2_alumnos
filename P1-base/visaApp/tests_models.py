# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# author: rmarabini

from django.test import TestCase
from django.db.utils import IntegrityError
from .models import Tarjeta, Pago, CodigoRespuesta
from .views import verificar_tarjeta, registrar_pago
# from datetime import datetime


class TarjetaModelTest(TestCase):

    def setUp(self):
        # Create a Tarjeta instance for testing
        self.tarjeta_data = {
            "numero": "1111 2222 3333 4444",
            "nombre": "Juan Perez",
            "fechaCaducidad": "12/30",
            "codigoAutorizacion": "ABC"
        }
        self.tarjeta = Tarjeta.objects.create(**self.tarjeta_data)

    def test_00_tarjeta_creation(self):
        """Test that a Tarjeta instance is created correctly."""
        self.assertEqual(self.tarjeta.numero, self.tarjeta_data["numero"])
        self.assertEqual(self.tarjeta.nombre, self.tarjeta_data["nombre"])
        self.assertEqual(self.tarjeta.fechaCaducidad,
                         self.tarjeta_data["fechaCaducidad"])
        self.assertEqual(self.tarjeta.codigoAutorizacion,
                         self.tarjeta_data["codigoAutorizacion"])
        self.assertEqual(str(self.tarjeta), "Juan Perez (Numero: 1111 2222 3333 4444)")

    def test_01_unique_numero(self):
        """Test that numero is unique."""
        with self.assertRaises(IntegrityError):
            Tarjeta.objects.create(
                numero=self.tarjeta_data["numero"],  # Duplicate numero
                nombre="Ana Lopez",
                fechaCaducidad="09/31",
                codigoAutorizacion="DEF"
            )


class PagoModelTest(TestCase):

    def setUp(self):
        # Create a Tarjeta instance
        self.tarjeta_data = {
            "numero": "1111 2222 3333 4444",
            "nombre": "Juan Perez",
            "fechaCaducidad": "12/30",
            "codigoAutorizacion": "ABC"
        }
        self.tarjeta = Tarjeta.objects.create(**self.tarjeta_data)
        self.pago_data = {
            "idComercio": "C001",
            "idTransaccion": "T001",
            "importe": 123.0,
            "tarjeta_id": self.tarjeta.numero,
            "codigoRespuesta": CodigoRespuesta.RESPUESTA_OK
            }

    def test_01_pago_creation(self):
        """Test that a Pago instance is created correctly."""
        pago = Pago.objects.create(**self.pago_data)

        self.assertEqual(pago.idComercio,
                         self.pago_data["idComercio"])
        self.assertEqual(pago.idTransaccion,
                         self.pago_data["idTransaccion"])
        self.assertEqual(pago.importe,
                         self.pago_data["importe"])
        self.assertEqual(pago.tarjeta, self.tarjeta)
        self.assertEqual(
            pago.codigoRespuesta, self.pago_data["codigoRespuesta"])
        self.assertEqual(str(pago), "Pago para C001 con importe 123.0")

    def test_02_default_codigo_respuesta(self):
        """Test that the default codigoRespuesta is RESPUESTA_OK."""
        pago = Pago.objects.create(
            idComercio ="C002",
            idTransaccion ="T002",
            importe = 123.0,
            tarjeta=self.tarjeta
        )
        self.assertEqual(pago.codigoRespuesta, CodigoRespuesta.RESPUESTA_OK)

    def test_03_unique_constraint(self):
        """Test that unique constraint
        on (idComercio, idTransaccion) is enforced."""
        Pago.objects.create(
            idComercio="C003",
            idTransaccion="T003",
            importe= 123.0,
            tarjeta=self.tarjeta
        )

        with self.assertRaises(IntegrityError):
            # Attempt to create another pago with the same
            # (idComercio, idTransaccion)
            Pago.objects.create(
                idComercio="C003",
                idTransaccion="T003",
                importe=123.0,
                tarjeta=self.tarjeta
            )


class VerificarTarjetaTests(TestCase):
    def setUp(self):
        # Create a Tarjeta instance
        self.tarjeta_data = {
            "numero": "1111 2222 3333 4444",
            "nombre": "Juan Perez",
            "fechaCaducidad": "12/30",
            "codigoAutorizacion": "ABC"
        }
        self.tarjeta = Tarjeta.objects.create(**self.tarjeta_data)

    def test_verificar_tarjeta_valid(self):
        # Test with valid data
        result = verificar_tarjeta(self.tarjeta_data)
        self.assertTrue(result)

    def test_verificar_tarjeta_invalid(self):
        # Test with invalid data
        self.tarjeta_data['numero'] = '0000 0000 0000 0000'
        result = verificar_tarjeta(self.tarjeta_data)
        self.assertFalse(result)


class RegistrarPagoTests(TestCase):
    def setUp(self):
        # Create a Tarjeta instance
        self.tarjeta_data = {
            "numero": "1111 2222 3333 4444",
            "nombre": "Juan Perez",
            "fechaCaducidad": "12/30",
            "codigoAutorizacion": "ABC"
        }
        self.tarjeta = Tarjeta.objects.create(**self.tarjeta_data)
        self.pago_data = {
            "idComercio": "C001",
            "idTransaccion": "T001",
            "importe": 123.0,
            "tarjeta_id": self.tarjeta.numero,
            "codigoRespuesta": CodigoRespuesta.RESPUESTA_OK
            }

    def test_registrar_pago_valid(self):
        # Test with valid vote data
        result = registrar_pago(self.pago_data)
        pago = result
        self.assertTrue(result)
        self.assertEqual(pago.importe,
                         self.pago_data["importe"])

    def test_registrar_pago_invalid(self):
        # The blank=False constraint and MinLengthValidator are enforced
        # when using Django forms (e.g., ModelForm), but if you create
        # or modify a Pago instance programmatically in Python code
        # (e.g., via Pago.objects.create()), the field's constraints
        # might not be validated unless explicitly checked.
        # So let us delete the foreignley to force an error in the "pago"
        # creation

        # Test with invalid vote data
        self.pago_data.pop("tarjeta_id")
        result = registrar_pago(self.pago_data)
        self.assertIsNone(result)
        # Check that the error message
        # mentions the missing field
