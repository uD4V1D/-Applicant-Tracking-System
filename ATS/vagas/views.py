from django.db.models import Q
from django.db.models.aggregates import Count
from django.db.models.functions import TruncMonth
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from candidaturas.models import Candidatura

from .models import Vaga
from .permissions import IsEmpresaOwnerOrReadOnly
from .serializers import VagaSerializer


class VagaViewSet(ModelViewSet):
    serializer_class = VagaSerializer
    permission_classes = (IsEmpresaOwnerOrReadOnly,)

    def get_queryset(self):
        queryset = Vaga.objects.select_related('empresa').order_by('-criada_em')
        user = self.request.user

        if not user.is_authenticated or user.tipo == 'candidato':
            queryset = queryset.filter(status='aberta')

        faixa_salarial = self.request.query_params.get('faixa_salarial')
        escolaridade_minima = self.request.query_params.get('escolaridade_minima')
        busca = self.request.query_params.get('q')

        if faixa_salarial:
            queryset = queryset.filter(faixa_salarial=faixa_salarial)
        if escolaridade_minima:
            queryset = queryset.filter(escolaridade_minima=escolaridade_minima)
        if busca:
            queryset = queryset.filter(Q(nome__icontains=busca) | Q(requisitos__icontains=busca))

        return queryset

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def minhas(self, request):
        if request.user.tipo != 'empresa':
            raise PermissionDenied('Apenas empresas podem acessar o gerenciamento de vagas.')
        queryset = (
            Vaga.objects.filter(empresa=request.user)
            .annotate(total_candidaturas=Count('candidatura'))
            .order_by('-criada_em')
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='relatorios/mensal',
    )
    def relatorios_mensal(self, request):
        if request.user.tipo != 'empresa':
            raise PermissionDenied('Apenas empresas podem acessar relatórios.')

        vagas_empresa_qs = Vaga.objects.filter(empresa=request.user)

        vagas_por_mes_qs = (
            vagas_empresa_qs
            .annotate(mes=TruncMonth('criada_em'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        candidaturas_por_mes_qs = (
            Candidatura.objects.filter(vaga__empresa=request.user)
            .annotate(mes=TruncMonth('data'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        vagas_status_por_mes_qs = (
            vagas_empresa_qs
            .annotate(mes=TruncMonth('criada_em'))
            .values('mes', 'status')
            .annotate(total=Count('id'))
            .order_by('mes', 'status')
        )
        candidaturas_por_vaga_qs = (
            vagas_empresa_qs
            .annotate(total_candidaturas=Count('candidatura'))
            .order_by('-total_candidaturas', 'nome')
            .values('id', 'nome', 'total_candidaturas')
        )

        vagas_por_mes = {
            item['mes'].strftime('%Y-%m'): item['total']
            for item in vagas_por_mes_qs
            if item['mes']
        }
        candidaturas_por_mes = {
            item['mes'].strftime('%Y-%m'): item['total']
            for item in candidaturas_por_mes_qs
            if item['mes']
        }
        status_por_mes = {'aberta': {}, 'encerrada': {}, 'preenchida': {}}
        for item in vagas_status_por_mes_qs:
            mes = item['mes']
            status = item['status']
            if not mes or status not in status_por_mes:
                continue
            status_por_mes[status][mes.strftime('%Y-%m')] = item['total']

        labels = sorted(
            set(vagas_por_mes.keys())
            | set(candidaturas_por_mes.keys())
            | set(status_por_mes['aberta'].keys())
            | set(status_por_mes['encerrada'].keys())
            | set(status_por_mes['preenchida'].keys())
        )
        return Response(
            {
                'labels': labels,
                'vagas_criadas_por_mes': [vagas_por_mes.get(label, 0) for label in labels],
                'candidatos_recebidos_por_mes': [candidaturas_por_mes.get(label, 0) for label in labels],
                'vagas_abertas_por_mes': [status_por_mes['aberta'].get(label, 0) for label in labels],
                'vagas_encerradas_por_mes': [status_por_mes['encerrada'].get(label, 0) for label in labels],
                'vagas_preenchidas_por_mes': [status_por_mes['preenchida'].get(label, 0) for label in labels],
                'candidaturas_por_vaga_labels': [f"#{item['id']} - {item['nome']}" for item in candidaturas_por_vaga_qs],
                'candidaturas_por_vaga': [item['total_candidaturas'] for item in candidaturas_por_vaga_qs],
            }
        )
