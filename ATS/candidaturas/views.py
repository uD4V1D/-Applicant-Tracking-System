from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView

from vagas.models import Vaga

from .models import Candidatura
from .serializers import CandidateProfileSerializer, CandidaturaSerializer


class CandidaturaListCreateView(ListCreateAPIView):
    serializer_class = CandidaturaSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.tipo != 'candidato':
            raise PermissionDenied('Apenas candidatos podem listar suas candidaturas.')
        return Candidatura.objects.filter(candidato=self.request.user).select_related('vaga').order_by('-data')

    def perform_create(self, serializer):
        if self.request.user.tipo != 'candidato':
            raise PermissionDenied('Apenas candidatos podem se candidatar.')
        serializer.save(candidato=self.request.user)


class VagaCandidaturasListView(ListAPIView):
    serializer_class = CandidaturaSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.tipo != 'empresa':
            raise PermissionDenied('Apenas empresas podem visualizar candidaturas da vaga.')
        vaga = get_object_or_404(Vaga, pk=self.kwargs['vaga_id'])
        if vaga.empresa_id != self.request.user.id:
            raise PermissionDenied('Você não possui acesso às candidaturas desta vaga.')
        return Candidatura.objects.filter(vaga=vaga).select_related('candidato').order_by('-data')


class CandidaturaPerfilCandidatoView(RetrieveAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        if self.request.user.tipo != 'empresa':
            raise PermissionDenied('Apenas empresas podem visualizar o perfil do candidato.')
        candidatura = get_object_or_404(
            Candidatura.objects.select_related('vaga', 'candidato').prefetch_related('candidato__perfilcandidato__experiencias'),
            pk=self.kwargs['candidatura_id'],
        )
        if candidatura.vaga.empresa_id != self.request.user.id:
            raise PermissionDenied('Você não possui acesso ao perfil deste candidato.')
        return candidatura.candidato
