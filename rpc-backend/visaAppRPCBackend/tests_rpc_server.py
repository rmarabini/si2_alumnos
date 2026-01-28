from django.test import TestCase, Client
from django.urls import reverse
import json
from .models import Tarjeta, Pago
from copy import deepcopy
from rest_framework import status


class RpcEndpointTestCase(TestCase):
    """
    Test suite for JSON-RPC endpoints related to Tarjeta and Pago operations.
    """

    def setUp(self):
        """Initialize common test data and Django test client."""
        # Django test client
        self.client = Client()

        # Sample tarjeta data
        self.tarjeta_data = {
            'numero': '1111 2222 3333 4444',
            'nombre': 'Jose Moreno Locke',
            'fechaCaducidad': '04/36',
            'codigoAutorizacion': '729'
        }

        # Sample pago data (tarjeta FK added when needed)
        self.pago_data = {
            "idComercio": "COM123",
            "idTransaccion": "TR123",
            "importe": 23.0,
        }

    def disable_test_rpc_addition(self):
        """
        (Disabled) Test a simple JSON-RPC arithmetic method.
        Used to validate the RPC infrastructure.
        """
        url = reverse('rpc')

        # JSON-RPC payload for test_add(5, 9)
        payload = {
            "id": 2,
            "method": "test_add",
            "params": [5, 9],
            "jsonrpc": "2.0"
        }

        # Send JSON-RPC request
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Parse response
        response_data = response.json()

        # Validate JSON-RPC response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_data.get('result'), 14)
        self.assertEqual(response_data.get('id'), payload['id'])
        self.assertEqual(response_data.get('jsonrpc'), "2.0")

    def test_00_rpc_pago(self):
        """Create a Pago using an RPC call."""
        url = reverse('rpc')

        # Create tarjeta required by foreign key
        Tarjeta.objects.create(**self.tarjeta_data)

        # Prepare pago data including tarjeta reference
        data = self.pago_data.copy()
        data['tarjeta_id'] = self.tarjeta_data['numero']

        payload = {
            "id": 2,
            "method": "registrar_pago",
            "params": {'pago_dict': data},
            "jsonrpc": "2.0"
        }

        # Send RPC request
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        # Validate response payload
        response_data = response.json()
        pago = response_data['result']

        for key, value in data.items():
            if key != 'tarjeta_id':
                self.assertEqual(pago[key], value)

    def test_01_rpc_tarjeta(self):
        """Verify tarjeta data using an RPC call."""
        url = reverse('rpc')

        # Insert tarjeta into database
        Tarjeta.objects.create(**self.tarjeta_data)

        payload = {
            "id": 2,
            "method": "verificar_tarjeta",
            "params": {'tarjeta_data': self.tarjeta_data},
            "jsonrpc": "2.0"
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json"
        )

        response_data = response.json()
        result = response_data.get('result')

        self.assertTrue(result)

    def test_10_del(self):
        """Delete an existing Pago using an RPC call."""
        # Create tarjeta and pago
        tarjeta = Tarjeta.objects.create(**self.tarjeta_data)
        pago = Pago.objects.create(**self.pago_data, tarjeta=tarjeta)

        payload = {
            "id": 10,
            "method": "eliminar_pago",
            "params": [pago.id],
            "jsonrpc": "2.0"
        }

        response = self.client.post(
            reverse('rpc'),
            data=json.dumps(payload),
            content_type="application/json"
        )

        response_data = response.json()
        self.assertTrue(response_data.get('result'))

    def test_20_list(self):
        """Retrieve pagos filtered by idComercio using RPC."""
        # Create tarjetas
        tarjeta1 = Tarjeta.objects.create(**self.tarjeta_data)

        tarjeta_data2 = self.tarjeta_data.copy()
        tarjeta_data2['numero'] = '123456789'
        tarjeta2 = Tarjeta.objects.create(**tarjeta_data2)

        # Create pagos
        Pago.objects.create(**self.pago_data, tarjeta=tarjeta1)

        pago_data2 = self.pago_data.copy()
        pago_data2['idTransaccion'] = 'B'
        Pago.objects.create(**pago_data2, tarjeta=tarjeta2)

        pago_data3 = deepcopy(self.pago_data)
        pago_data3['idComercio'] = 'C'
        Pago.objects.create(**pago_data3, tarjeta=tarjeta2)

        payload = {
            "id": 10,
            "method": "get_pagos_from_db",
            "params": [self.pago_data['idComercio']],
            "jsonrpc": "2.0"
        }

        response = self.client.post(
            reverse('rpc'),
            data=json.dumps(payload),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_data = response.json()
        result = response_data.get('result')

        # Only pagos with matching idComercio should be returned
        self.assertEqual(len(result), 2)

