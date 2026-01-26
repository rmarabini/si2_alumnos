from django.shortcuts import redirect, render
from visaApp.forms import PagoForm, TarjetaForm, DelPagoForm, GetPagosForm
from visaApp.pagoDB import (verificar_tarjeta, registrar_pago,
                            eliminar_pago, get_pagos_from_db)


TITLE = '(visaSite)'


# Create your views here.

def aportarinfo_pago(request):
    if request.method == 'POST':
        # data from form
        pago_form = PagoForm(request.POST)
        pago_form.get_context()

        # recoger variable de session

        if 'numeroTarjeta' in request.session:
            numero = request.session['numeroTarjeta']
        else:
            return render(
                request, 'template_mensaje.html',
                {'mensaje': '¡Error: numero tarjeta no encontrado en la sesión!',
                 'title': TITLE})
        pago_data = pago_form.cleaned_data
        # add numero to data
        pago_data['tarjeta_id'] = numero
        # save pago and get updated pago
        pago = registrar_pago(pago_data)
        if pago is None:
            return render(request, 'template_mensaje.html',
                          {'mensaje': '¡Error: al registrar pago!',
                           'title': TITLE})
        context_dict = {'pago': pago, 'title': TITLE}
        return render(request, 'template_exito.html', context_dict)
    else:
        pago_form = PagoForm()
        context_dict = {'form': pago_form, 'title': TITLE}
        return render(request, 'template_pago.html', context_dict)


def aportarinfo_tarjeta(request):

    if request.method == 'POST':

        tarjeta_form = TarjetaForm(request.POST)
        tarjeta_form.get_context()

        if verificar_tarjeta(tarjeta_form.cleaned_data) is False:
            return render(
                request, 'template_mensaje.html',
                {'mensaje': '¡Error: Tarjeta no registrada!',
                 'title': TITLE})

        # Guardamos el DNI
        request.session['numeroTarjeta'] = tarjeta_form.cleaned_data['numero']
        return redirect('pago')

    else:

        tarjeta_form = TarjetaForm()
        context_dict = {'form': tarjeta_form, 'title': TITLE}

        return render(request, 'template_tarjeta.html', context_dict)


def testbd(request):

    if request.method == 'POST':

        pago_form = PagoForm(request.POST)
        tarjeta_form = TarjetaForm(request.POST)
        tarjeta_form.get_context()
        pago_form.get_context()

        if verificar_tarjeta(tarjeta_form.cleaned_data) is False:
            return render(
                request, 'template_mensaje.html',
                {'mensaje': '¡Error: Tarjeta no registrada!',
                 'title': TITLE})

        data = pago_form.cleaned_data
        data['tarjeta_id'] = tarjeta_form.cleaned_data['numero']

        # save pago

        pago = registrar_pago(data)

        if pago is None:
            return render(
                request, 'template_mensaje.html',
                {'mensaje': 'Error al registrar pago!',
                 'title': TITLE})

        context_dict = {'pago': pago, 'title': TITLE}

        return render(request, 'template_exito.html', context_dict)
    else:
        pago_form = PagoForm()
        del_pago_form = DelPagoForm()
        tarjeta_form = TarjetaForm()
        get_pagos_form = GetPagosForm()

        return render(request, 'template_test_bd.html',
                      {'pago_form': pago_form,
                       'tarjeta_form': tarjeta_form,
                       'del_pago_form': del_pago_form,
                       'get_pagos_form': get_pagos_form,
                       'title': TITLE})


def delpago(request):

    if request.method == 'POST':
        del_pago_form = DelPagoForm(request.POST)
        if del_pago_form.is_valid():
            id = del_pago_form.cleaned_data['id']
            if eliminar_pago(id) is False:
                return render(request, 'template_mensaje.html',
                              {'mensaje': '¡Error: al elminar pago!',
                               'title': TITLE})
            return render(request, 'template_mensaje.html',
                          {'mensaje': '¡Pago eliminado correctamente!',
                           'title': TITLE})


def getpagos(request):
    if request.method == 'POST':
        get_pagos_form = GetPagosForm(request.POST)
        if get_pagos_form.is_valid():
            idComercio =get_pagos_form.cleaned_data['idComercio']
            pagos = get_pagos_from_db(idComercio)
            return render(request, 'template_get_pagos_result.html',
                          {'result': pagos, 'title': TITLE})
