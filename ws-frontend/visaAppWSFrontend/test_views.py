# ----------------------------------------------------------------------
# Common test code for client applications
#
# This test suite covers both REST API endpoints and RCP procedures.
#
# NOTE:
# We cannot use the standard Django test database because it is
# different from the database used by the REST API server or the
# RCP machine. Therefore, these tests require a direct connection
# to the target PostgreSQL database.
#
# Author: Roberto Marabini
# ----------------------------------------------------------------------

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from rest_framework import status
import psycopg2


class PagoViewsTest(TestCase):
    """
    Test suite for Pago-related API views and RCP procedures.
    """

    def setUp(self):
        """Initialize test client and database connection."""
        # Django test client
        self.client = Client()

        # Direct database connection (not Django test DB)
        connection_string = settings.DATABASE_SERVER_URL
        self.connection = psycopg2.connect(connection_string)
        self.cursor = self.connection.cursor()

        # Clean pago table before each test
        self.cursor.execute("DELETE FROM pago;")
        self.connection.commit()

        # Default tarjeta test data
        self.tarjeta_data = {
            'numero': '23',
            'nombre': '23',
            'fechaCaducidad': '23',
            'codigoAutorizacion': '23'
        }

        # Ensure tarjeta exists in database
        self.insertTarjeta(self.tarjeta_data)

        # Default valid pago data
        self.pago_valid_data = {
            "idComercio": "COM123",
            "idTransaccion": "TR123",
            "importe": 23.0,
            "tarjeta_id": "23"
        }

        # URL endpoints
        self.url_pago_store = reverse('pago')
        self.url_tarjeta_check = reverse('tarjeta')
        self.url_testbd = reverse('testbd')

    def verifypagoCreation(self, numeroTarjeta):
        """
        Verify whether a pago exists for a given tarjeta number.

        Returns:
            (count, pago_id) or (0, None) if not found
        """
        query = f"SELECT * FROM pago WHERE tarjeta_id='{numeroTarjeta}';"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        if len(rows) == 0:
            return 0, None

        return len(rows), rows[0][0]

    def insertPago(self, pago_data):
        """Insert a pago record directly into the database."""
        insert_pago_query = """
        INSERT INTO pago (
            "idComercio",
            "idTransaccion",
            "importe",
            "marcaTiempo",
            "codigoRespuesta",
            "tarjeta_id"
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(
            insert_pago_query,
            (
                pago_data["idComercio"],
                pago_data["idTransaccion"],
                pago_data["importe"],
                pago_data["marcaTiempo"],
                pago_data["codigoRespuesta"],
                pago_data["tarjeta_id"],
            )
        )
        self.connection.commit()

    def insertTarjeta(self, tarjeta_data):
        """Insert tarjeta record if it does not already exist."""
        insert_tarjeta_query = """
        INSERT INTO tarjeta (
            "numero",
            nombre,
            "fechaCaducidad",
            "codigoAutorizacion"
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT ("numero") DO NOTHING;
        """
        self.cursor.execute(
            insert_tarjeta_query,
            (
                tarjeta_data["numero"],
                tarjeta_data["nombre"],
                tarjeta_data["fechaCaducidad"],
                tarjeta_data["codigoAutorizacion"],
            )
        )
        self.connection.commit()

    def test_01_aportarinfo_tarjeta_valid_post(self):
        """Test valid tarjeta submission."""
        response = self.client.post(reverse('tarjeta'), self.tarjeta_data)

        # Expect redirect to pago view
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, reverse('pago'))

        # Verify session data
        session = self.client.session
        self.assertEqual(session['numeroTarjeta'], self.tarjeta_data['numero'])

    def test_015_aportarinfo_tarjeta_invalid_post(self):
        """Test invalid tarjeta submission."""
        data = self.tarjeta_data.copy()
        data['numero'] = '845rtte34'  # invalid tarjeta number

        response = self.client.post(reverse('tarjeta'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("Error" in str(response.content))

    def test_02_store_pago_valid_post(self):
        """Test valid pago creation via API."""
        # Simulate prior tarjeta submission
        session = self.client.session
        session['numeroTarjeta'] = self.tarjeta_data['numero']
        session.save()

        response = self.client.post(
            reverse('pago'),
            data=self.pago_valid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validate returned pago data
        pago = response.context.get('pago')
        for key in self.pago_valid_data:
            if key != 'tarjeta_id':
                self.assertEqual(self.pago_valid_data[key], pago[key])

    def test_03_delpago_valid_post(self):
        """Test deletion of an existing pago."""
        pago_data = {
            **self.pago_valid_data,
            'marcaTiempo': '2022-01-01 00:00:00',
            'codigoRespuesta': '000',
            'tarjeta_id': self.tarjeta_data['numero']
        }
        self.insertPago(pago_data)

        _, pago_id = self.verifypagoCreation(self.tarjeta_data['numero'])

        response = self.client.post(reverse('delpago'), {'id': pago_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Pago eliminado correctamente")

    def test_035_delpago_invalid_post(self):
        """Test deletion of a non-existing pago."""
        response = self.client.post(reverse('delpago'), {'id': 999999998})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Error")

    def test_04_getPagos_post(self):
        """Test retrieval of pagos filtered by comercio."""
        # Insert tarjetas
        for numero in ['83583583', '67867868']:
            self.tarjeta_data['numero'] = numero
            self.insertTarjeta(self.tarjeta_data)

        # Insert pagos
        pagos = [
            ('aaaaa0', 'COM123', self.tarjeta_data['numero']),
            ('aaaaa1', 'c0', '83583583'),
            ('aaaaa2', 'c0', '67867868'),
        ]

        for transaccion, comercio, tarjeta in pagos:
            self.insertPago({
                **self.pago_valid_data,
                'idTransaccion': transaccion,
                'idComercio': comercio,
                'marcaTiempo': '2022-01-01 00:00:00',
                'codigoRespuesta': '000',
                'tarjeta_id': tarjeta
            })

        response = self.client.post(reverse('getpagos'), {'idComercio': 'c0'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "aaaaa1")
        self.assertContains(response, "aaaaa2")
        self.assertNotContains(response, "aaaaa0")

    def test_10_testdb_post(self):
        """Test combined tarjeta + pago submission."""
        data = {**self.tarjeta_data, **self.pago_valid_data}

        response = self.client.post(reverse('testbd'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        pago = response.context.get('pago')
        for key in self.pago_valid_data:
            if key != 'tarjeta_id':
                self.assertEqual(self.pago_valid_data[key], pago[key])

    def test_11_testdb_invalid_post(self):
        """Test testdb endpoint with missing tarjeta data."""
        response = self.client.post(
            reverse('testbd'),
            data=self.pago_valid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Error")
