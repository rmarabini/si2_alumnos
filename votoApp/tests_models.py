# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# author: rmarabini

from django.test import TestCase
from django.db.utils import IntegrityError
from .models import Censo, Voto, CodigoRespuesta
from .views import verificar_censo, registrar_voto
# from datetime import datetime


class CensoModelTest(TestCase):

    def setUp(self):
        # Create a Censo instance for testing
        self.censo_data = {
            "numeroDNI": "123456789",
            "nombre": "Juan Perez",
            "fechaNacimiento": "19900101",
            "anioCenso": "2024",
            "codigoAutorizacion": "ABC"
        }
        self.censo = Censo.objects.create(**self.censo_data)

    def test_00_censo_creation(self):
        """Test that a Censo instance is created correctly."""
        self.assertEqual(self.censo.numeroDNI, self.censo_data["numeroDNI"])
        self.assertEqual(self.censo.nombre, self.censo_data["nombre"])
        self.assertEqual(self.censo.fechaNacimiento,
                         self.censo_data["fechaNacimiento"])
        self.assertEqual(self.censo.anioCenso, self.censo_data["anioCenso"])
        self.assertEqual(self.censo.codigoAutorizacion,
                         self.censo_data["codigoAutorizacion"])
        self.assertEqual(str(self.censo), "Juan Perez (DNI: 123456789)")

    def test_01_unique_numeroDNI(self):
        """Test that numeroDNI is unique."""
        with self.assertRaises(IntegrityError):
            Censo.objects.create(
                numeroDNI=self.censo_data["numeroDNI"],  # Duplicate DNI
                nombre="Ana Lopez",
                fechaNacimiento="19851231",
                anioCenso="2024",
                codigoAutorizacion="DEF"
            )


class VotoModelTest(TestCase):

    def setUp(self):
        # Create a Censo instance
        self.censo_data = {
            "numeroDNI": "123456789",
            "nombre": "Juan Perez",
            "fechaNacimiento": "19900101",
            "anioCenso": "2024",
            "codigoAutorizacion": "ABC"
        }
        self.censo = Censo.objects.create(**self.censo_data)
        self.voto_data = {
            "idCircunscripcion": "C001",
            "idMesaElectoral": "M001",
            "idProcesoElectoral": "P001",
            "nombreCandidatoVotado": "Candidato A",
            "censo_id": self.censo.numeroDNI,
            "codigoRespuesta": CodigoRespuesta.RESPUESTA_OK
            }

    def test_01_voto_creation(self):
        """Test that a Voto instance is created correctly."""
        voto = Voto.objects.create(**self.voto_data)

        self.assertEqual(voto.idCircunscripcion,
                         self.voto_data["idCircunscripcion"])
        self.assertEqual(voto.idMesaElectoral,
                         self.voto_data["idMesaElectoral"])
        self.assertEqual(voto.idProcesoElectoral,
                         self.voto_data["idProcesoElectoral"])
        self.assertEqual(voto.nombreCandidatoVotado,
                         self.voto_data["nombreCandidatoVotado"])
        self.assertEqual(voto.censo, self.censo)
        self.assertEqual(
            voto.codigoRespuesta, self.voto_data["codigoRespuesta"])
        self.assertEqual(str(voto), "Voto para Candidato A en proceso P001")

    def test_02_default_codigo_respuesta(self):
        """Test that the default codigoRespuesta is RESPUESTA_OK."""
        voto = Voto.objects.create(
            idCircunscripcion="C002",
            idMesaElectoral="M002",
            idProcesoElectoral="P002",
            nombreCandidatoVotado="Candidato B",
            censo=self.censo
        )
        self.assertEqual(voto.codigoRespuesta, CodigoRespuesta.RESPUESTA_OK)

    def test_03_unique_constraint(self):
        """Test that unique constraint
        on (censo, idProcesoElectoral) is enforced."""
        Voto.objects.create(
            idCircunscripcion="C003",
            idMesaElectoral="M003",
            idProcesoElectoral="P003",
            nombreCandidatoVotado="Candidato C",
            censo=self.censo
        )

        with self.assertRaises(IntegrityError):
            # Attempt to create another vote with the same
            # (censo, idProcesoElectoral)
            Voto.objects.create(
                idCircunscripcion="C004",
                idMesaElectoral="M004",
                idProcesoElectoral="P003",
                nombreCandidatoVotado="Candidato D",
                censo=self.censo
            )


class VerificarCensoTests(TestCase):
    def setUp(self):
        # Create a Censo instance
        self.censo_data = {
            "numeroDNI": "123456789",
            "nombre": "Juan Perez",
            "fechaNacimiento": "19900101",
            "anioCenso": "2024",
            "codigoAutorizacion": "ABC"
        }
        self.censo = Censo.objects.create(**self.censo_data)
        # self.voto_data = {
        #     "idCircunscripcion": "C001",
        #     "idMesaElectoral": "M001",
        #     "idProcesoElectoral": "P001",
        #     "nombreCandidatoVotado": "Candidato A",
        #     "censo_id": self.censo.numeroDNI,
        #     "codigoRespuesta": CodigoRespuesta.RESPUESTA_OK
        #     }

    def test_verificar_censo_valid(self):
        # Test with valid data
        result = verificar_censo(self.censo_data)
        self.assertTrue(result)

    def test_verificar_censo_invalid(self):
        # Test with invalid data
        self.censo_data['numeroDNI'] = '000000000'
        result = verificar_censo(self.censo_data)
        self.assertFalse(result)


class RegistrarVotoTests(TestCase):
    def setUp(self):
        # Create a Censo instance
        self.censo_data = {
            "numeroDNI": "123456789",
            "nombre": "Juan Perez",
            "fechaNacimiento": "19900101",
            "anioCenso": "2024",
            "codigoAutorizacion": "ABC"
        }
        self.censo = Censo.objects.create(**self.censo_data)
        self.voto_data = {
            "idCircunscripcion": "C001",
            "idMesaElectoral": "M001",
            "idProcesoElectoral": "P001",
            "nombreCandidatoVotado": "Candidato A",
            "censo_id": self.censo.numeroDNI,
            "codigoRespuesta": CodigoRespuesta.RESPUESTA_OK
            }

    def test_registrar_voto_valid(self):
        # Test with valid vote data
        result = registrar_voto(self.voto_data)
        voto = result
        self.assertTrue(result)
        self.assertEqual(voto.nombreCandidatoVotado,
                         self.voto_data["nombreCandidatoVotado"])

    def test_registrar_voto_invalid(self):
        # The blank=False constraint and MinLengthValidator are enforced
        # when using Django forms (e.g., ModelForm), but if you create
        # or modify a Voto instance programmatically in Python code
        # (e.g., via Voto.objects.create()), the field's constraints
        # might not be validated unless explicitly checked.
        # So let us delete the foreignley to force an error in the "voto"
        # creation

        # Test with invalid vote data
        self.voto_data.pop("censo_id")
        result = registrar_voto(self.voto_data)
        self.assertIsNone(result)
        # self.assertTrue('null value in column "censo_id"' in str(error))
        # Check that the error message
        # mentions the missing field
