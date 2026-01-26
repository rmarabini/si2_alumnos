# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import Pago, Tarjeta


class VisaViewsTest(TestCase):
    def setUp(self):
        # create virtual browser
        self.client = Client()

        # populate the database
        # from common.management.commands.populate import Command
        # Command().handle()

        # Set up initial test data
        self.tarjeta_data = {
            'numero': '1111 2222 3333 4444',
            'nombre': 'Jose Moreno Locke',
            'fechaCaducidad': '04/28',
            'codigoAutorizacion': '729'
        }

        self.tarjeta = Tarjeta.objects.create(
            **self.tarjeta_data
        )

        self.pago_data = {
            'idComercio': 'IDC123',
            'idTransaccion': 'IDT123',
            'importe': 123.0
        }

        # URL endpoints for views
        self.aportarinfo_pago_url = reverse('pago')
        self.aportarinfo_tarjeta_url = reverse('tarjeta')
        self.testbd_url = reverse('testbd')
        self.delpago_url = reverse('delpago')
        self.getpagos_url = reverse('getpagos')

    def test_00_aportarinfo_tarjeta_valid_submission(self):
        # Post valid data to `aportarinfo_pago` view
        response = self.client.post(self.aportarinfo_tarjeta_url,
                                    data=self.tarjeta_data)

        # Check if data is saved in the session
        session_data = self.client.session['numeroTarjeta']
        self.assertEqual(session_data, self.tarjeta_data['numero'])
        # Check if redirected to `pago` page
        self.assertRedirects(response, reverse('pago'))

    def test_01_aportarinfo_tarjeta_invalid_submission(self):
        # Submit empty form data
        response = self.client.post(
            self.aportarinfo_tarjeta_url, data={})
        self.assertIn('Error', str(response.content))

    def test_05_aportarinfo_pago_with_valid_tarjeta_data(self):
        # Set up session data with valid tarjeta data
        session = self.client.session
        session['numeroTarjeta'] = self.tarjeta.numero
        session.save()

        # Submit valid Pago data
        response = self.client.post(
            self.aportarinfo_pago_url, data=self.pago_data)
        # Check if pago was created
        # print("response: ", response.content)
        self.assertTrue(Pago.objects.filter(tarjeta=self.tarjeta).exists())
        self.assertTemplateUsed(response, 'template_exito.html')

    def test_06_aportarinfo_pago_without_tarjeta_data(self):
        # Submit valid Pago data without tarjeta_data in session
        response = self.client.post(self.aportarinfo_pago_url,
                                    data=self.pago_data)
        # print("response: ", response.content)
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, 'Error')

    def test_10_testbd_valid_submission(self):
        # Submit valid data for both Pago and Tarjeta forms
        combined_data = {**self.pago_data, **self.tarjeta_data}
        response = self.client.post(self.testbd_url, data=combined_data)

        # Verify Pago creation
        self.assertTrue(Pago.objects.filter(tarjeta=self.tarjeta).exists())
        self.assertTemplateUsed(response, 'template_exito.html')

    def test_15_delpago_valid_deletion(self):
        # Create a Pago instance to delete
        pago = Pago.objects.create(tarjeta=self.tarjeta , **self.pago_data)

        # Submit the deletion form
        response = self.client.post(self.delpago_url, data={'id': pago.id})
        self.assertFalse(Pago.objects.filter(id=pago.id).exists())
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, '¡Pago eliminado correctamente!')

    def test_20_delpago_invalid_id(self):
        # Submit with a non-existing ID
        response = self.client.post(self.delpago_url, data={'id': 999})
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, 'Error:')

    def test_25_getpagos_valid_idComercio(self):
        # Create two Pago instances for the same idComercio
        Pago.objects.create(tarjeta=self.tarjeta, **self.pago_data)
        # Submit a GetPagosForm with a valid idProcesoElectoral
        response = self.client.post(
            self.getpagos_url, data={'idComercio': 'IDC123'})
        self.assertEqual(len(response.context['result']), 1)
        self.assertTemplateUsed(response, 'template_get_pagos_result.html')

    def test_30_testbd_invalid_submission(self):
        # Submit empty form data
        response = self.client.post(self.testbd_url, data={})
        self.assertIn('Error', str(response.content))
