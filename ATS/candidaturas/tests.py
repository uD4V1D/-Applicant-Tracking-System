import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import ExperienciaProfissional, PerfilCandidato
from candidaturas.models import Candidatura
from vagas.models import Vaga

User = get_user_model()


def auth_client_for(user):
    client = APIClient()
    token_response = client.post(
        '/api/auth/login/',
        {'email': user.email, 'password': 'senhaforte123'},
        format='json',
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")
    return client


def create_candidate_with_profile(email='cand@x.com'):
    candidate = User.objects.create_user(
        email=email,
        password='senhaforte123',
        tipo='candidato',
        nome_completo='Candidato Teste',
        data_nascimento='1995-01-01',
    )
    PerfilCandidato.objects.create(
        user=candidate,
        pretensao_salarial=3000,
        experiencia='Experiência em desenvolvimento',
        escolaridade='superior',
    )
    return candidate


@pytest.mark.django_db
def test_candidate_can_apply_only_once():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile()
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='DevOps',
        faixa_salarial='4',
        requisitos='AWS',
        escolaridade_minima='superior',
    )
    client = auth_client_for(candidato)

    first = client.post('/api/candidaturas/', {'vaga': vaga.id}, format='json')
    second = client.post('/api/candidaturas/', {'vaga': vaga.id}, format='json')

    assert first.status_code == 201
    assert second.status_code == 400
    assert Candidatura.objects.filter(candidato=candidato, vaga=vaga).count() == 1


@pytest.mark.django_db
def test_empresa_cannot_apply():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='Data Engineer',
        faixa_salarial='4',
        requisitos='SQL',
        escolaridade_minima='superior',
    )
    client = auth_client_for(empresa)

    response = client.post('/api/candidaturas/', {'vaga': vaga.id}, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_candidate_cannot_apply_to_closed_or_filled_vaga():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile()
    vaga_encerrada = Vaga.objects.create(
        empresa=empresa,
        nome='Product Owner',
        faixa_salarial='4',
        requisitos='Agile',
        escolaridade_minima='superior',
        status='encerrada',
    )
    vaga_preenchida = Vaga.objects.create(
        empresa=empresa,
        nome='Tech Lead',
        faixa_salarial='4',
        requisitos='Liderança técnica',
        escolaridade_minima='superior',
        status='preenchida',
    )
    client = auth_client_for(candidato)

    closed_response = client.post('/api/candidaturas/', {'vaga': vaga_encerrada.id}, format='json')
    filled_response = client.post('/api/candidaturas/', {'vaga': vaga_preenchida.id}, format='json')

    assert closed_response.status_code == 400
    assert filled_response.status_code == 400


@pytest.mark.django_db
def test_candidate_lists_own_candidaturas():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile()
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='Mobile',
        faixa_salarial='3',
        requisitos='Flutter',
        escolaridade_minima='tecnologo',
    )
    Candidatura.objects.create(candidato=candidato, vaga=vaga)
    client = auth_client_for(candidato)

    response = client.get('/api/candidaturas/')
    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_empresa_lists_candidaturas_for_own_vaga():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    outra_empresa = User.objects.create_user(email='outra@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile()
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='SRE',
        faixa_salarial='4',
        requisitos='Kubernetes',
        escolaridade_minima='superior',
    )
    Candidatura.objects.create(candidato=candidato, vaga=vaga)

    owner_client = auth_client_for(empresa)
    other_client = auth_client_for(outra_empresa)

    allowed = owner_client.get(f'/api/vagas/{vaga.id}/candidaturas/')
    denied = other_client.get(f'/api/vagas/{vaga.id}/candidaturas/')

    assert allowed.status_code == 200
    assert allowed.data['count'] == 1
    assert allowed.data['results'][0]['candidato_nome'] == 'Candidato Teste'
    assert denied.status_code == 403


@pytest.mark.django_db
def test_candidate_without_profile_cannot_apply():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    candidato = User.objects.create_user(email='semperfil@x.com', password='senhaforte123', tipo='candidato')
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='Backend',
        faixa_salarial='3',
        requisitos='Python',
        escolaridade_minima='superior',
    )

    client = auth_client_for(candidato)
    response = client.post('/api/candidaturas/', {'vaga': vaga.id}, format='json')

    assert response.status_code == 400
    assert 'Complete o perfil de candidato' in str(response.data)


@pytest.mark.django_db
def test_empresa_can_open_candidate_profile_from_candidatura():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile(email='perfil@x.com')
    ExperienciaProfissional.objects.create(
        perfil=candidato.perfilcandidato,
        nome_empresa='Empresa XPTO',
        data_inicio='2020-01-01',
        data_saida='2022-01-01',
        principais_responsabilidades='Desenvolvimento backend',
        emprego_atual=False,
    )
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='Backend Python',
        faixa_salarial='4',
        requisitos='Django',
        escolaridade_minima='superior',
    )
    candidatura = Candidatura.objects.create(candidato=candidato, vaga=vaga)

    client = auth_client_for(empresa)
    response = client.get(f'/api/candidaturas/{candidatura.id}/perfil-candidato/')

    assert response.status_code == 200
    assert response.data['email'] == candidato.email
    assert response.data['nome_completo'] == candidato.nome_completo
    assert response.data['pretensao_salarial'] == 3000
    assert len(response.data['experiencias']) == 1
    assert response.data['experiencias'][0]['nome_empresa'] == 'Empresa XPTO'


@pytest.mark.django_db
def test_other_empresa_cannot_open_candidate_profile_from_candidatura():
    empresa = User.objects.create_user(email='empresa@x.com', password='senhaforte123', tipo='empresa')
    outra_empresa = User.objects.create_user(email='outra@x.com', password='senhaforte123', tipo='empresa')
    candidato = create_candidate_with_profile(email='acesso@x.com')
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='QA',
        faixa_salarial='2',
        requisitos='Testes',
        escolaridade_minima='medio',
    )
    candidatura = Candidatura.objects.create(candidato=candidato, vaga=vaga)

    client = auth_client_for(outra_empresa)
    response = client.get(f'/api/candidaturas/{candidatura.id}/perfil-candidato/')

    assert response.status_code == 403
