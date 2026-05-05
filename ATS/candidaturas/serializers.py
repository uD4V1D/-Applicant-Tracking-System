from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from accounts.models import ExperienciaProfissional

from .models import Candidatura

User = get_user_model()


class CandidaturaSerializer(serializers.ModelSerializer):
    candidato_email = serializers.EmailField(source='candidato.email', read_only=True)
    candidato_nome = serializers.SerializerMethodField()

    class Meta:
        model = Candidatura
        fields = ('id', 'vaga', 'data', 'candidato_email', 'candidato_nome')
        read_only_fields = ('id', 'data', 'candidato_email', 'candidato_nome')

    def get_candidato_nome(self, obj):
        return obj.candidato.nome_completo or obj.candidato.email

    def validate(self, attrs):
        request = self.context['request']
        vaga = attrs['vaga']
        if request.user.tipo != 'candidato':
            raise serializers.ValidationError('Apenas candidatos podem se candidatar.')
        try:
            request.user.perfilcandidato
        except ObjectDoesNotExist:
            raise serializers.ValidationError('Complete o perfil de candidato antes de se candidatar.')
        if vaga.status != 'aberta':
            raise serializers.ValidationError('A vaga não está aberta para candidatura.')
        if Candidatura.objects.filter(candidato=request.user, vaga=vaga).exists():
            raise serializers.ValidationError('Você já se candidatou para esta vaga.')
        return attrs


class CandidateExperienciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienciaProfissional
        fields = (
            'nome_empresa',
            'data_inicio',
            'data_saida',
            'principais_responsabilidades',
            'emprego_atual',
        )


class CandidateProfileSerializer(serializers.ModelSerializer):
    pretensao_salarial = serializers.SerializerMethodField()
    escolaridade = serializers.SerializerMethodField()
    experiencias = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'nome_completo',
            'email',
            'data_nascimento',
            'pretensao_salarial',
            'escolaridade',
            'experiencias',
        )

    def _get_perfil(self, obj):
        try:
            return obj.perfilcandidato
        except ObjectDoesNotExist:
            return None

    def get_pretensao_salarial(self, obj):
        perfil = self._get_perfil(obj)
        return perfil.pretensao_salarial if perfil else None

    def get_escolaridade(self, obj):
        perfil = self._get_perfil(obj)
        return perfil.escolaridade if perfil else None

    def get_experiencias(self, obj):
        perfil = self._get_perfil(obj)
        if not perfil:
            return []
        experiencias = perfil.experiencias.all().order_by('-criada_em')
        return CandidateExperienciaSerializer(experiencias, many=True).data
