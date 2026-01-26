# your_app/management/commands/populate.py

import csv
import os
from django.core.management.base import BaseCommand
from visaApp.models import Tarjeta, Pago


class Command(BaseCommand):
    help = 'Populate the database with data from a CSV file'

    def handle(self, *args, **kwargs):
        self.cleanDataBase()
        self.populateDataBase()

    def cleanDataBase(self):
        # Delete all existing records from the database
        Tarjeta.objects.all().delete()
        Pago.objects.all().delete()
        print("Database cleaned successfully")

    def populateDataBase(self):
        """Populate the database with data from a CSV file
        numero,nombre,fechaCaducidad,codigoAutorizacion
        1111 2222 3333 4444,Jose Moreno Locke,09/66,729
        """
        csv_file_path = os.path.join(os.path.dirname(__file__), 'data.csv')
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Iterating over each row in the CSV
            for row in reader:
                # Create or update the Tarjeta instance based on the numero
                Tarjeta.objects.update_or_create(
                    numero=row['numero'],
                    defaults={
                        'nombre': row['nombre'],
                        'fechaCaducidad': row['fechaCaducidad'],
                        'codigoAutorizacion': row['codigoAutorizacion']
                    }
                )
        print("Tarjeta objects created successfully")
