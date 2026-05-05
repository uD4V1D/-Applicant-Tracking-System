import re
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from .models import ExperienciaProfissional, PerfilCandidato, PerfilEmpresa

User = get_user_model()


def _normalize_cnpj(value):
    return re.sub(r'\D', '', value or '')


class UserSerializer(serializers.ModelSerializer):
    candidate_profile_completed = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    cnpj = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'tipo',
            'nome_completo',
            'data_nascimento',
            'candidate_profile_completed',
            'nome_empresa',
            'cnpj',
        )
        read_only_fields = ('id',)

    def get_candidate_profile_completed(self, obj):
        if obj.tipo != 'candidato':
            return True
        try:
            obj.perfilcandidato
            return True
        except ObjectDoesNotExist:
            return False

    def get_nome_empresa(self, obj):
        if obj.tipo != 'empresa':
            return None
        perfil = getattr(obj, 'perfil_empresa', None)
        return perfil.nome_empresa if perfil else None

    def get_cnpj(self, obj):
        if obj.tipo != 'empresa':
            return None
        perfil = getattr(obj, 'perfil_empresa', None)
        return perfil.cnpj if perfil else None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    nome_empresa = serializers.CharField(required=False, allow_blank=False)
    cnpj = serializers.CharField(required=False, allow_blank=False)
    nome_completo = serializers.CharField(required=False, allow_blank=False)
    data_nascimento = serializers.DateField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'password',
            'tipo',
            'nome_completo',
            'data_nascimento',
            'nome_empresa',
            'cnpj',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        tipo = attrs.get('tipo')
        if tipo == 'candidato':
            nome_completo = attrs.get('nome_completo')
            data_nascimento = attrs.get('data_nascimento')
            if not nome_completo:
                raise serializers.ValidationError({'nome_completo': 'Nome completo é obrigatório para candidato.'})
            if not data_nascimento:
                raise serializers.ValidationError({'data_nascimento': 'Data de nascimento é obrigatória para candidato.'})
            if data_nascimento > date.today():
                raise serializers.ValidationError({'data_nascimento': 'Data de nascimento não pode ser superior à data atual.'})
        elif tipo == 'empresa':
            nome_empresa = attrs.get('nome_empresa')
            cnpj = _normalize_cnpj(attrs.get('cnpj'))
            if not nome_empresa:
                raise serializers.ValidationError({'nome_empresa': 'Nome da empresa é obrigatório.'})
            if not cnpj:
                raise serializers.ValidationError({'cnpj': 'CNPJ é obrigatório.'})
            if len(cnpj) != 14:
                raise serializers.ValidationError({'cnpj': 'CNPJ deve conter 14 dígitos.'})
            attrs['cnpj'] = cnpj
            if PerfilEmpresa.objects.filter(cnpj=cnpj).exists():
                raise serializers.ValidationError({'cnpj': 'Este CNPJ já está cadastrado.'})
        else:
            raise serializers.ValidationError({'tipo': 'Tipo de usuário inválido.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        nome_empresa = validated_data.pop('nome_empresa', None)
        cnpj = validated_data.pop('cnpj', None)
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user.tipo == 'empresa':
            PerfilEmpresa.objects.create(user=user, nome_empresa=nome_empresa, cnpj=cnpj)
        return user


class UserProfileReadSerializer(UserSerializer):
    pass


class UserProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=False, allow_blank=False, min_length=8, write_only=True)
    nome_completo = serializers.CharField(required=False, allow_blank=False)
    data_nascimento = serializers.DateField(required=False)
    nome_empresa = serializers.CharField(required=False, allow_blank=False)
    cnpj = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        user = self.instance
        if user is None:
            raise serializers.ValidationError('Usuário inválido.')

        email = attrs.get('email')
        if not email:
            raise serializers.ValidationError({'email': 'E-mail é obrigatório.'})
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise serializers.ValidationError({'email': 'Este e-mail já está em uso.'})

        if user.tipo == 'candidato':
            nome_completo = attrs.get('nome_completo')
            data_nascimento = attrs.get('data_nascimento')
            if not nome_completo:
                raise serializers.ValidationError({'nome_completo': 'Nome completo é obrigatório.'})
            if not data_nascimento:
                raise serializers.ValidationError({'data_nascimento': 'Data de nascimento é obrigatória.'})
            if data_nascimento > date.today():
                raise serializers.ValidationError({'data_nascimento': 'Data de nascimento não pode ser superior à data atual.'})
        elif user.tipo == 'empresa':
            nome_empresa = attrs.get('nome_empresa')
            cnpj = _normalize_cnpj(attrs.get('cnpj'))
            if not nome_empresa:
                raise serializers.ValidationError({'nome_empresa': 'Nome da empresa é obrigatório.'})
            if not cnpj:
                raise serializers.ValidationError({'cnpj': 'CNPJ é obrigatório.'})
            if len(cnpj) != 14:
                raise serializers.ValidationError({'cnpj': 'CNPJ deve conter 14 dígitos.'})
            attrs['cnpj'] = cnpj
            if PerfilEmpresa.objects.filter(cnpj=cnpj).exclude(user=user).exists():
                raise serializers.ValidationError({'cnpj': 'Este CNPJ já está cadastrado.'})

        return attrs

    def update(self, instance, validated_data):
        instance.email = validated_data['email']
        if instance.tipo == 'candidato':
            instance.nome_completo = validated_data['nome_completo']
            instance.data_nascimento = validated_data['data_nascimento']
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()

        if instance.tipo == 'empresa':
            perfil_empresa, _ = PerfilEmpresa.objects.get_or_create(user=instance)
            perfil_empresa.nome_empresa = validated_data['nome_empresa']
            perfil_empresa.cnpj = validated_data['cnpj']
            perfil_empresa.save()

        return instance


class ExperienciaProfissionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienciaProfissional
        fields = (
            'id',
            'nome_empresa',
            'data_inicio',
            'data_saida',
            'principais_responsabilidades',
            'emprego_atual',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        emprego_atual = attrs.get('emprego_atual', False)
        data_inicio = attrs.get('data_inicio')
        data_saida = attrs.get('data_saida')
        today = date.today()

        if data_inicio and data_inicio > today:
            raise serializers.ValidationError(
                {'data_inicio': 'Data de início não pode ser superior à data atual.'}
            )
        if data_saida and data_saida > today:
            raise serializers.ValidationError(
                {'data_saida': 'Data de saída não pode ser superior à data atual.'}
            )

        if emprego_atual and data_saida:
            raise serializers.ValidationError(
                {'data_saida': 'Para emprego atual, a data de saída não pode ser preenchida.'}
            )

        if data_inicio and data_saida and data_saida < data_inicio:
            raise serializers.ValidationError(
                {'data_saida': 'A data de saída não pode ser anterior à data de início.'}
            )

        return attrs


class PerfilCandidatoSerializer(serializers.ModelSerializer):
    experiencias = ExperienciaProfissionalSerializer(many=True, required=False)

    class Meta:
        model = PerfilCandidato
        fields = ('pretensao_salarial', 'escolaridade', 'experiencias')

    def validate_pretensao_salarial(self, value):
        if value < 0:
            raise serializers.ValidationError('A pretensão salarial não pode ser menor que zero.')
        return value

    def validate_experiencias(self, value):
        total_emprego_atual = sum(1 for experiencia in value if experiencia.get('emprego_atual'))
        if total_emprego_atual > 1:
            raise serializers.ValidationError('Apenas uma experiência pode ser marcada como emprego atual.')
        return value

    def _sync_experiencias(self, profile, experiencias):
        profile.experiencias.all().delete()
        for experiencia in experiencias:
            ExperienciaProfissional.objects.create(perfil=profile, **experiencia)

    def create(self, validated_data):
        experiencias = validated_data.pop('experiencias', [])
        profile = PerfilCandidato.objects.create(**validated_data)
        self._sync_experiencias(profile, experiencias)
        return profile

    def update(self, instance, validated_data):
        experiencias = validated_data.pop('experiencias', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if experiencias is not None:
            self._sync_experiencias(instance, experiencias)

        return instance
