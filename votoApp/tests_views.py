# tests.py
from django.test import TestCase, Client
from django.urls import reverse
from .models import Voto, Censo
# from .forms import VotoForm, CensoForm, DelVotoForm, GetVotosForm


class VotoCensoViewsTest(TestCase):
    def setUp(self):
        # create virtual browser
        self.client = Client()

        # populate the database
        # from common.management.commands.populate import Command
        # Command().handle()

        # Set up initial test data
        self.censo_data = {
            'numeroDNI': '39739740E',
            'nombre': 'Jose Moreno Locke',
            'fechaNacimiento': '09/04/66',
            'anioCenso': '2025',
            'codigoAutorizacion': '729'
        }

        self.censo = Censo.objects.create(
            **self.censo_data
        )

        self.voto_data = {
            'idCircunscripcion': 'CIRC123',
            'idMesaElectoral': 'MESA123',
            'idProcesoElectoral': 'ELEC123',
            'nombreCandidatoVotado': 'Candidate A'
        }

        # URL endpoints for views
        self.aportarinfo_voto_url = reverse('voto')
        self.aportarinfo_censo_url = reverse('censo')
        self.testbd_url = reverse('testbd')
        self.delvoto_url = reverse('delvoto')
        self.getvotos_url = reverse('getvotos')

    def test_00_aportarinfo_censo_valid_submission(self):
        # Post valid data to `aportarinfo_voto` view
        response = self.client.post(self.aportarinfo_censo_url,
                                    data=self.censo_data)

        # Check if data is saved in the session
        session_data = self.client.session['numeroDNI']
        self.assertEqual(session_data, self.censo_data['numeroDNI'])
        # Check if redirected to `voto` page
        self.assertRedirects(response, reverse('voto'))

    def test_01_aportarinfo_censo_invalid_submission(self):
        # Submit empty form data
        response = self.client.post(
            self.aportarinfo_censo_url, data={})
        self.assertIn('Error', str(response.content))

    def test_05_aportarinfo_voto_with_valid_censo_data(self):
        # Set up session data with valid censo data
        session = self.client.session
        session['numeroDNI'] = self.censo.numeroDNI
        session.save()

        # Submit valid Voto data
        response = self.client.post(
            self.aportarinfo_voto_url, data=self.voto_data)
        # Check if voto was created
        # print("response: ", response.content)
        self.assertTrue(Voto.objects.filter(censo=self.censo).exists())
        self.assertTemplateUsed(response, 'template_exito.html')

    def test_06_aportarinfo_voto_without_censo_data(self):
        # Submit valid Voto data without censo_data in session
        response = self.client.post(self.aportarinfo_voto_url,
                                    data=self.voto_data)
        # print("response: ", response.content)
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, 'Error')

    def test_10_testbd_valid_submission(self):
        # Submit valid data for both Voto and Censo forms
        combined_data = {**self.voto_data, **self.censo_data}
        response = self.client.post(self.testbd_url, data=combined_data)

        # Verify Voto creation
        self.assertTrue(Voto.objects.filter(censo=self.censo).exists())
        self.assertTemplateUsed(response, 'template_exito.html')

    def test_15_delvoto_valid_deletion(self):
        # Create a Voto instance to delete
        voto = Voto.objects.create(censo=self.censo, **self.voto_data)

        # Submit the deletion form
        response = self.client.post(self.delvoto_url, data={'id': voto.id})
        self.assertFalse(Voto.objects.filter(id=voto.id).exists())
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, '¡Voto eliminado correctamente!')

    def test_20_delvoto_invalid_id(self):
        # Submit with a non-existing ID
        response = self.client.post(self.delvoto_url, data={'id': 999})
        self.assertTemplateUsed(response, 'template_mensaje.html')
        self.assertContains(response, 'Error:')

    def test_25_getvotos_valid_idProcesoElectoral(self):
        # Create two Voto instances for the same proceso electoral
        Voto.objects.create(censo=self.censo, **self.voto_data)
        # Submit a GetVotosForm with a valid idProcesoElectoral
        response = self.client.post(
            self.getvotos_url, data={'idProcesoElectoral': 'ELEC123'})
        self.assertEqual(len(response.context['result']), 1)
        self.assertTemplateUsed(response, 'template_get_votos_result.html')

    def test_30_testbd_invalid_submission(self):
        # Submit empty form data
        response = self.client.post(self.testbd_url, data={})
        self.assertIn('Error', str(response.content))
