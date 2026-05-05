"""
URL configuration for ATS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.auth import CustomTokenObtainPairView

urlpatterns = [
    path('', TemplateView.as_view(template_name='portal.html'), name='ui-home'),
    path('portal/', TemplateView.as_view(template_name='portal.html'), name='ui-portal'),
    path('cadastro/', TemplateView.as_view(template_name='cadastro.html'), name='ui-cadastro'),
    path('empresa/', TemplateView.as_view(template_name='empresa.html'), name='ui-empresa'),
    path('perfil/', TemplateView.as_view(template_name='perfil.html'), name='ui-perfil'),
    path('vaga/<int:vaga_id>/', TemplateView.as_view(template_name='vaga_detalhe.html'), name='ui-vaga-detalhe'),
    path('relatorios/', TemplateView.as_view(template_name='relatorios.html'), name='ui-relatorios'),
    path('gestao-vaga/', TemplateView.as_view(template_name='gestao_vaga.html'), name='ui-gestao-vaga'),
    path('admin/', admin.site.urls),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('accounts.urls')),
    path('api/', include('vagas.urls')),
    path('api/', include('candidaturas.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
