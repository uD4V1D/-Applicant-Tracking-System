from django.urls import path

from .views import CandidaturaListCreateView, CandidaturaPerfilCandidatoView, VagaCandidaturasListView

urlpatterns = [
    path('candidaturas/', CandidaturaListCreateView.as_view(), name='candidaturas'),
    path('vagas/<int:vaga_id>/candidaturas/', VagaCandidaturasListView.as_view(), name='vaga-candidaturas'),
    path(
        'candidaturas/<int:candidatura_id>/perfil-candidato/',
        CandidaturaPerfilCandidatoView.as_view(),
        name='candidatura-perfil-candidato',
    ),
]
