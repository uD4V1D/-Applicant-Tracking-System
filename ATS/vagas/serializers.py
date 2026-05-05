from rest_framework import serializers

from .models import Vaga


class VagaSerializer(serializers.ModelSerializer):
    empresa_id = serializers.IntegerField(source='empresa.id', read_only=True)
    empresa_email = serializers.EmailField(source='empresa.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_candidaturas = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Vaga
        fields = (
            'id',
            'nome',
            'faixa_salarial',
            'requisitos',
            'escolaridade_minima',
            'status',
            'status_display',
            'criada_em',
            'empresa_id',
            'empresa_email',
            'total_candidaturas',
        )
        read_only_fields = ('id', 'criada_em', 'empresa_id', 'empresa_email', 'status_display', 'total_candidaturas')
