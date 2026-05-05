import pytest
from datetime import datetime, timezone as dt_timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

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


@pytest.mark.django_db
def test_only_empresa_can_create_vaga():
    candidato = User.objects.create_user(email='cand@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(candidato)

    response = client.post(
        '/api/vagas/',
        {
            'nome': 'Desenvolvedor Python',
            'faixa_salarial': '4',
            'requisitos': 'Django e DRF',
            'escolaridade_minima': 'superior',
        },
        format='json',
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_empresa_owner_can_update_vaga_but_other_cannot():
    empresa_a = User.objects.create_user(email='a@empresa.com', password='senhaforte123', tipo='empresa')
    empresa_b = User.objects.create_user(email='b@empresa.com', password='senhaforte123', tipo='empresa')
    vaga = Vaga.objects.create(
        empresa=empresa_a,
        nome='Backend JR',
        faixa_salarial='3',
        requisitos='Python',
        escolaridade_minima='medio',
    )

    owner_client = auth_client_for(empresa_a)
    other_client = auth_client_for(empresa_b)

    own_update = owner_client.patch(f'/api/vagas/{vaga.id}/', {'nome': 'Backend Pleno'}, format='json')
    assert own_update.status_code == 200
    assert own_update.data['nome'] == 'Backend Pleno'

    forbidden_update = other_client.patch(f'/api/vagas/{vaga.id}/', {'nome': 'Tentativa indevida'}, format='json')
    assert forbidden_update.status_code == 403


@pytest.mark.django_db
def test_vagas_listing_is_public():
    empresa = User.objects.create_user(email='empresa@empresa.com', password='senhaforte123', tipo='empresa')
    Vaga.objects.create(
        empresa=empresa,
        nome='QA',
        faixa_salarial='2',
        requisitos='Testes',
        escolaridade_minima='medio',
    )

    client = APIClient()
    response = client.get('/api/vagas/')

    assert response.status_code == 200
    assert response.data['count'] == 1


@pytest.mark.django_db
def test_candidate_and_public_listing_hide_closed_and_filled_positions():
    empresa = User.objects.create_user(email='empresa@empresa.com', password='senhaforte123', tipo='empresa')
    Vaga.objects.create(
        empresa=empresa,
        nome='Desenvolvedor Backend',
        faixa_salarial='4',
        requisitos='Python e Django',
        escolaridade_minima='superior',
        status='aberta',
    )
    Vaga.objects.create(
        empresa=empresa,
        nome='Analista de Dados',
        faixa_salarial='3',
        requisitos='SQL',
        escolaridade_minima='superior',
        status='encerrada',
    )
    Vaga.objects.create(
        empresa=empresa,
        nome='UX Designer',
        faixa_salarial='3',
        requisitos='Figma',
        escolaridade_minima='superior',
        status='preenchida',
    )

    public_client = APIClient()
    candidate = User.objects.create_user(email='cand@empresa.com', password='senhaforte123', tipo='candidato')
    candidate_client = auth_client_for(candidate)

    public_response = public_client.get('/api/vagas/')
    candidate_response = candidate_client.get('/api/vagas/')

    assert public_response.status_code == 200
    assert candidate_response.status_code == 200
    assert public_response.data['count'] == 1
    assert candidate_response.data['count'] == 1
    assert public_response.data['results'][0]['status'] == 'aberta'


@pytest.mark.django_db
def test_empresa_can_list_own_vagas_including_closed_and_filled():
    empresa = User.objects.create_user(email='empresa@empresa.com', password='senhaforte123', tipo='empresa')
    outra_empresa = User.objects.create_user(email='outra@empresa.com', password='senhaforte123', tipo='empresa')
    Vaga.objects.create(
        empresa=empresa,
        nome='Dev Frontend',
        faixa_salarial='3',
        requisitos='React',
        escolaridade_minima='superior',
        status='encerrada',
    )
    Vaga.objects.create(
        empresa=empresa,
        nome='Dev Fullstack',
        faixa_salarial='4',
        requisitos='Node e Django',
        escolaridade_minima='superior',
        status='preenchida',
    )
    Vaga.objects.create(
        empresa=outra_empresa,
        nome='Dev iOS',
        faixa_salarial='4',
        requisitos='Swift',
        escolaridade_minima='superior',
        status='aberta',
    )

    client = auth_client_for(empresa)
    response = client.get('/api/vagas/minhas/')

    assert response.status_code == 200
    assert len(response.data) == 2
    returned_ids = {item['nome'] for item in response.data}
    assert returned_ids == {'Dev Frontend', 'Dev Fullstack'}


@pytest.mark.django_db
def test_keyword_search_looks_at_name_and_description():
    empresa = User.objects.create_user(email='empresa@empresa.com', password='senhaforte123', tipo='empresa')
    Vaga.objects.create(
        empresa=empresa,
        nome='Analista QA',
        faixa_salarial='2',
        requisitos='Automação de testes com Python',
        escolaridade_minima='tecnologo',
        status='aberta',
    )
    Vaga.objects.create(
        empresa=empresa,
        nome='Designer',
        faixa_salarial='2',
        requisitos='Figma e UX',
        escolaridade_minima='tecnologo',
        status='aberta',
    )

    client = APIClient()
    response = client.get('/api/vagas/?q=python')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['nome'] == 'Analista QA'


@pytest.mark.django_db
def test_empresa_can_get_monthly_reports():
    empresa = User.objects.create_user(email='empresa@empresa.com', password='senhaforte123', tipo='empresa')
    candidato_1 = User.objects.create_user(email='cand1@empresa.com', password='senhaforte123', tipo='candidato')
    candidato_2 = User.objects.create_user(email='cand2@empresa.com', password='senhaforte123', tipo='candidato')

    vaga_jan = Vaga.objects.create(
        empresa=empresa,
        nome='Backend JR',
        faixa_salarial='3',
        requisitos='Python',
        escolaridade_minima='medio',
        status='aberta',
    )
    vaga_fev = Vaga.objects.create(
        empresa=empresa,
        nome='Frontend JR',
        faixa_salarial='3',
        requisitos='React',
        escolaridade_minima='medio',
        status='encerrada',
    )
    vaga_mar = Vaga.objects.create(
        empresa=empresa,
        nome='Data JR',
        faixa_salarial='3',
        requisitos='SQL',
        escolaridade_minima='medio',
        status='preenchida',
    )

    Vaga.objects.filter(id=vaga_jan.id).update(criada_em=datetime(2026, 1, 10, tzinfo=dt_timezone.utc))
    Vaga.objects.filter(id=vaga_fev.id).update(criada_em=datetime(2026, 2, 10, tzinfo=dt_timezone.utc))
    Vaga.objects.filter(id=vaga_mar.id).update(criada_em=datetime(2026, 3, 10, tzinfo=dt_timezone.utc))

    cand_jan = Candidatura.objects.create(candidato=candidato_1, vaga=vaga_jan)
    cand_mar_1 = Candidatura.objects.create(candidato=candidato_1, vaga=vaga_mar)
    cand_mar_2 = Candidatura.objects.create(candidato=candidato_2, vaga=vaga_mar)
    Candidatura.objects.filter(id=cand_jan.id).update(data=datetime(2026, 1, 15, tzinfo=dt_timezone.utc))
    Candidatura.objects.filter(id=cand_mar_1.id).update(data=datetime(2026, 3, 15, tzinfo=dt_timezone.utc))
    Candidatura.objects.filter(id=cand_mar_2.id).update(data=datetime(2026, 3, 20, tzinfo=dt_timezone.utc))

    client = auth_client_for(empresa)
    response = client.get('/api/vagas/relatorios/mensal/')

    assert response.status_code == 200
    assert response.data['labels'] == ['2026-01', '2026-02', '2026-03']
    assert response.data['vagas_criadas_por_mes'] == [1, 1, 1]
    assert response.data['candidatos_recebidos_por_mes'] == [1, 0, 2]
    assert response.data['vagas_abertas_por_mes'] == [1, 0, 0]
    assert response.data['vagas_encerradas_por_mes'] == [0, 1, 0]
    assert response.data['vagas_preenchidas_por_mes'] == [0, 0, 1]
    candidaturas_por_vaga = dict(
        zip(response.data['candidaturas_por_vaga_labels'], response.data['candidaturas_por_vaga'])
    )
    assert candidaturas_por_vaga[f'#{vaga_jan.id} - {vaga_jan.nome}'] == 1
    assert candidaturas_por_vaga[f'#{vaga_fev.id} - {vaga_fev.nome}'] == 0
    assert candidaturas_por_vaga[f'#{vaga_mar.id} - {vaga_mar.nome}'] == 2


@pytest.mark.django_db
def test_candidate_cannot_get_monthly_reports():
    candidato = User.objects.create_user(email='cand@empresa.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(candidato)
    response = client.get('/api/vagas/relatorios/mensal/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_minhas_vagas_returns_candidate_count():
    empresa = User.objects.create_user(email='empresa-count@empresa.com', password='senhaforte123', tipo='empresa')
    candidato_1 = User.objects.create_user(email='cand-count-1@empresa.com', password='senhaforte123', tipo='candidato')
    candidato_2 = User.objects.create_user(email='cand-count-2@empresa.com', password='senhaforte123', tipo='candidato')
    vaga = Vaga.objects.create(
        empresa=empresa,
        nome='Backend Contagem',
        faixa_salarial='3',
        requisitos='Python',
        escolaridade_minima='superior',
        status='aberta',
    )
    Candidatura.objects.create(candidato=candidato_1, vaga=vaga)
    Candidatura.objects.create(candidato=candidato_2, vaga=vaga)

    client = auth_client_for(empresa)
    response = client.get('/api/vagas/minhas/')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['total_candidaturas'] == 2
