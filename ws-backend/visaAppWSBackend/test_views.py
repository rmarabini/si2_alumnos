# Test for web services related to payment and card operations.
# implemented as a REST API using Django REST Framework.
# this tests check the P1 backend implementation.
from copy import deepcopy
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Tarjeta, Pago
from .serializers import PagoSerializer
# from django.forms.models import model_to_dict

# ApiViewTest is a Django test case designed to verify the behavior of
# the REST API
# endpoints related to payment (Pago) and card (Tarjeta) operations.
# It uses Django REST Framework’s APIClient to simulate HTTP
# requests and validate
# both successful workflows and error conditions.


class ApiViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url_pago_store = reverse('pago')
        self.url_tarjeta_check = reverse('tarjeta')
        # self.url_testbd = reverse('testbd')

        self.pago_valid_data = {
            "idComercio": "COM123",
            "idTransaccion": "TR123",
            "importe": 123.0,
            "tarjeta_id": "123456789"
        }

        self.pago_invalid_data = {
            "idComercio": "COM123",
            # Missing 'idTransacción'
            "importe": 123.0,
            "tarjeta_id": "123456789"
        }

        self.tarjeta_data = {
            'numero': '1111 2222 3333 4444',
            'nombre': 'Jose Moreno Locke',
            'fechaCaducidad': '04/36',
            'codigoAutorizacion': '729'
        }
        self.tarjeta = Tarjeta.objects.create(**self.tarjeta_data)

    def test_01_tarjeta_check_valid_data(self):
        # Test storing valid data
        response = self.client.post(
            self.url_tarjeta_check,
            data=self.tarjeta_data,  # tarjeta data
            format='json'
        )
        # Check if the response is 200 OK and the message matches
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(), {'message': 'Datos encontrados en la base de datos'})

    def test_02_tarjeta_check_invalid_data(self):
        # Test checking tarjeta with  invalid data (missing fields)
        self.tarjeta_data['numero'] = '1234'
        response = self.client.post(
            self.url_tarjeta_check,
            data=self.tarjeta_data,  # tarjeta data
            format='json'
        )
        # Check if the response is not found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Confirm that no data was found
        self.assertEqual(
            response.json(), {'message': 'Datos no encontrados en la base de datos'})

    def test_05_list_pagos(self):
        # create another tarjeta entry. There is one with id=1111 2222 3333 4444
        # stored in self.tarjeta
        self.pago_valid_data.pop('tarjeta_id')
        self.tarjeta_data['numero'] = '2222 3333 4444 5555'
        tarjeta2 = Tarjeta.objects.create(**self.tarjeta_data)
        # create pago entry
        _ = Pago.objects.create(**self.pago_valid_data, tarjeta=self.tarjeta)
        # create another pago entry
        self.pago_valid_data['idComercio'] = "COM234"
        _ = Pago.objects.create(**self.pago_valid_data, tarjeta=tarjeta2)
        another_pago = deepcopy(self.pago_valid_data)
        another_pago['idTransaccion'] = 'TR234'
        _ = Pago.objects.create(**another_pago, tarjeta=tarjeta2)

        url = reverse(
            'comercio',
            args=[self.pago_valid_data['idComercio']])
        response = self.client.get(url)
        # Ensure the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the response data
        pagos = Pago.objects.filter(
            idComercio=self.pago_valid_data['idComercio'])
        serializer = PagoSerializer(pagos, many=True)
        self.assertEqual(response.data, serializer.data)

    def test_10_pago_store(self):

        # Test storing valid data
        self.pago_valid_data['tarjeta_id'] = '1111 2222 3333 4444'
        response = self.client.post(
            reverse('pago'),
            data=self.pago_valid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for k, v in self.pago_valid_data.items():
            if k == 'tarjeta_id':
                break
            self.assertEqual(v, response.data[k])

    def test_20_delete_existing_pago(self):
        """Test deleting an existing Pago object."""
        # create pago entry
        pago = Pago.objects.create(
            **self.pago_valid_data, tarjeta=self.tarjeta)
        # Build the delete URL using the ID of the created Pago instance
        url = reverse('pago', args=[pago.id])
        _ = self.client.delete(url)

        # Verify that the Pago instance has been deleted from the database
        self.assertFalse(Pago.objects.filter(id=pago.id).exists())

    def test_21_delete_nonexistent_pago(self):
        """Test attempting to delete a Pago object that does not exist."""
        # Build the delete URL using an ID that doesn't exist
        url = reverse('pago', args=[1234567])
        response = self.client.delete(url)

        # Check that the response status is 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
