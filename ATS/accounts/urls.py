from django.urls import path

from .views import MeView, PerfilCandidatoView, RegisterView, UserProfileView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('candidatos/perfil/', PerfilCandidatoView.as_view(), name='perfil-candidato'),
]
