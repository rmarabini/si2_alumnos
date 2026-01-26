from django import forms

class PagoForm(forms.Form):
    idComercio = forms.CharField(
        label='ID Comercio', required=True)
    idTransaccion = forms.CharField(
        label='ID Transaccion', required=True)
    importe = forms.FloatField(
        label='Importe', required=True)


class TarjetaForm(forms.Form):
    numero = forms.CharField(label="Número de Tarjeta", required=True)
    nombre = forms.CharField(label="Nombre", required=True)
    fechaCaducidad = forms.CharField(
        label="Fecha de Caducidad", required=True)
    codigoAutorizacion = forms.CharField(
        label="Código de Autorización", required=True)


class DelPagoForm(forms.Form):
    id = forms.CharField(label="ID del Pago", required=True)


class GetPagosForm(forms.Form):
    idComercio = forms.CharField(
        label='ID del Comercio', required=True)
