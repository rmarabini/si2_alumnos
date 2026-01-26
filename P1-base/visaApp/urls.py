"""
URL configuration for PagoProj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from visaApp.views import (aportarinfo_tarjeta, aportarinfo_pago,
                           testbd, getpagos, delpago)

urlpatterns = [
    path("", aportarinfo_tarjeta, name="index"),
    path("tarjeta/", aportarinfo_tarjeta, name="tarjeta"),
    path("pago/", aportarinfo_pago, name="pago"),
    path("testbd/", testbd, name="testbd"),
    path("testbd/getpagos/", getpagos, name="getpagos"),
    path("testbd/delpago/", delpago, name="delpago"),
]
