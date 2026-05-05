import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import PerfilCandidato

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def auth_client_for(user):
    client = APIClient()
    response = client.post(
        '/api/auth/login/',
        {'email': user.email, 'password': 'senhaforte123'},
        format='json',
    )
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.mark.django_db
def test_register_user(api_client):
    response = api_client.post(
        '/api/auth/register/',
        {
            'email': 'novo@exemplo.com',
            'password': 'senhaforte123',
            'tipo': 'candidato',
            'nome_completo': 'Novo Usuario',
            'data_nascimento': '1995-10-10',
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['email'] == 'novo@exemplo.com'
    assert 'password' not in response.data


@pytest.mark.django_db
def test_register_empresa_with_cnpj(api_client):
    response = api_client.post(
        '/api/auth/register/',
        {
            'email': 'empresa@exemplo.com',
            'password': 'senhaforte123',
            'tipo': 'empresa',
            'nome_empresa': 'Folzeck',
            'cnpj': '12.345.678/0001-99',
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['tipo'] == 'empresa'


@pytest.mark.django_db
def test_register_candidate_rejects_future_birth_date(api_client):
    response = api_client.post(
        '/api/auth/register/',
        {
            'email': 'futuro@exemplo.com',
            'password': 'senhaforte123',
            'tipo': 'candidato',
            'nome_completo': 'Pessoa Futuro',
            'data_nascimento': '2999-01-01',
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'data_nascimento' in response.data


@pytest.mark.django_db
def test_login_and_me_endpoint(api_client):
    user = User.objects.create_user(
        email='user@exemplo.com',
        password='senhaforte123',
        tipo='candidato',
        nome_completo='User Exemplo',
        data_nascimento='1990-01-01',
    )

    login = api_client.post(
        '/api/auth/login/',
        {'email': user.email, 'password': 'senhaforte123'},
        format='json',
    )

    assert login.status_code == 200
    assert 'access' in login.data
    assert 'refresh' in login.data

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api_client.get('/api/auth/me/')
    assert me.status_code == 200
    assert me.data['email'] == user.email
    assert me.data['candidate_profile_completed'] is False


@pytest.mark.django_db
def test_login_error_when_email_not_found(api_client):
    response = api_client.post(
        '/api/auth/login/',
        {'email': 'inexistente@exemplo.com', 'password': 'qualquer123'},
        format='json',
    )

    assert response.status_code == 401
    assert 'Usuário não encontrado' in response.data['detail']


@pytest.mark.django_db
def test_login_error_when_password_is_wrong(api_client):
    User.objects.create_user(email='user@exemplo.com', password='senhacorreta123', tipo='candidato')

    response = api_client.post(
        '/api/auth/login/',
        {'email': 'user@exemplo.com', 'password': 'senhaerrada123'},
        format='json',
    )

    assert response.status_code == 401
    assert 'Senha incorreta' in response.data['detail']


@pytest.mark.django_db
def test_candidate_profile_completion_is_true_when_profile_exists(api_client):
    user = User.objects.create_user(email='cand@exemplo.com', password='senhaforte123', tipo='candidato')
    PerfilCandidato.objects.create(
        user=user,
        pretensao_salarial=3500,
        escolaridade='superior',
    )

    login = api_client.post(
        '/api/auth/login/',
        {'email': user.email, 'password': 'senhaforte123'},
        format='json',
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    me = api_client.get('/api/auth/me/')

    assert me.status_code == 200
    assert me.data['candidate_profile_completed'] is True


@pytest.mark.django_db
def test_candidate_can_create_and_update_profile():
    user = User.objects.create_user(email='cand@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    create = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 3500,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Tech A',
                    'data_inicio': '2021-01-01',
                    'data_saida': '2023-01-01',
                    'principais_responsabilidades': 'Desenvolvimento backend e APIs',
                    'emprego_atual': False,
                }
            ],
        },
        format='json',
    )
    assert create.status_code == 200
    assert create.data['pretensao_salarial'] == 3500
    assert len(create.data['experiencias']) == 1
    assert create.data['experiencias'][0]['nome_empresa'] == 'Tech A'

    update = client.patch('/api/candidatos/perfil/', {'pretensao_salarial': 4000}, format='json')
    assert update.status_code == 200
    assert update.data['pretensao_salarial'] == 4000
    assert len(update.data['experiencias']) == 1


@pytest.mark.django_db
def test_profile_persists_experiencias_data():
    user = User.objects.create_user(email='candpersist@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    save_response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 5000,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Empresa Persist',
                    'data_inicio': '2020-01-01',
                    'data_saida': '2022-01-01',
                    'principais_responsabilidades': 'Arquitetura e APIs',
                    'emprego_atual': False,
                }
            ],
        },
        format='json',
    )
    assert save_response.status_code == 200

    get_response = client.get('/api/candidatos/perfil/')
    assert get_response.status_code == 200
    assert len(get_response.data['experiencias']) == 1
    assert get_response.data['experiencias'][0]['nome_empresa'] == 'Empresa Persist'


@pytest.mark.django_db
def test_profile_experience_rejects_data_saida_for_current_job():
    user = User.objects.create_user(email='cand2@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 3200,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Tech B',
                    'data_inicio': '2022-03-01',
                    'data_saida': '2024-01-01',
                    'principais_responsabilidades': 'Atuação em produto',
                    'emprego_atual': True,
                }
            ],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'data_saida' in str(response.data)


@pytest.mark.django_db
def test_profile_rejects_invalid_escolaridade_value():
    user = User.objects.create_user(email='cand3@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 4500,
            'escolaridade': 'qualquer',
            'experiencias': [],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'escolaridade' in response.data


@pytest.mark.django_db
def test_profile_rejects_negative_salary():
    user = User.objects.create_user(email='cand4@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': -1,
            'escolaridade': 'superior',
            'experiencias': [],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'pretensao_salarial' in response.data


@pytest.mark.django_db
def test_profile_accepts_zero_salary():
    user = User.objects.create_user(email='cand5@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 0,
            'escolaridade': 'superior',
            'experiencias': [],
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['pretensao_salarial'] == 0


@pytest.mark.django_db
def test_profile_rejects_experience_end_date_before_start_date():
    user = User.objects.create_user(email='cand6@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 2500,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Tech C',
                    'data_inicio': '2024-01-01',
                    'data_saida': '2023-01-01',
                    'principais_responsabilidades': 'Manutenção de sistemas',
                    'emprego_atual': False,
                }
            ],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'data_saida' in str(response.data)


@pytest.mark.django_db
def test_profile_rejects_experience_dates_after_today():
    user = User.objects.create_user(email='cand8@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 2500,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Tech Future',
                    'data_inicio': '2999-01-01',
                    'principais_responsabilidades': 'Planejamento',
                    'emprego_atual': True,
                }
            ],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'data_inicio' in str(response.data)


@pytest.mark.django_db
def test_profile_rejects_multiple_current_jobs():
    user = User.objects.create_user(email='cand7@exemplo.com', password='senhaforte123', tipo='candidato')
    client = auth_client_for(user)

    response = client.put(
        '/api/candidatos/perfil/',
        {
            'pretensao_salarial': 3500,
            'escolaridade': 'superior',
            'experiencias': [
                {
                    'nome_empresa': 'Empresa A',
                    'data_inicio': '2020-01-01',
                    'principais_responsabilidades': 'Backend',
                    'emprego_atual': True,
                },
                {
                    'nome_empresa': 'Empresa B',
                    'data_inicio': '2022-01-01',
                    'principais_responsabilidades': 'Arquitetura',
                    'emprego_atual': True,
                },
            ],
        },
        format='json',
    )

    assert response.status_code == 400
    assert 'Apenas uma experiência' in str(response.data)


@pytest.mark.django_db
def test_candidate_user_profile_update():
    user = User.objects.create_user(
        email='candprofile@exemplo.com',
        password='senhaforte123',
        tipo='candidato',
        nome_completo='Candidato Antigo',
        data_nascimento='1994-01-01',
    )
    client = auth_client_for(user)

    response = client.put(
        '/api/auth/profile/',
        {
            'email': 'candnovo@exemplo.com',
            'nome_completo': 'Candidato Novo',
            'data_nascimento': '1994-02-01',
            'password': 'novasenha123',
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['email'] == 'candnovo@exemplo.com'
    assert response.data['nome_completo'] == 'Candidato Novo'


@pytest.mark.django_db
def test_company_user_profile_update():
    register_client = APIClient()
    register_client.post(
        '/api/auth/register/',
        {
            'email': 'empresa2@exemplo.com',
            'password': 'senhaforte123',
            'tipo': 'empresa',
            'nome_empresa': 'Empresa Antiga',
            'cnpj': '12345678000190',
        },
        format='json',
    )
    user = User.objects.get(email='empresa2@exemplo.com')
    client = auth_client_for(user)

    response = client.put(
        '/api/auth/profile/',
        {
            'email': 'empresa2novo@exemplo.com',
            'nome_empresa': 'Empresa Nova',
            'cnpj': '12345678000191',
            'password': 'novasenha123',
        },
        format='json',
    )

    assert response.status_code == 200
    assert response.data['email'] == 'empresa2novo@exemplo.com'
    assert response.data['nome_empresa'] == 'Empresa Nova'


@pytest.mark.django_db
def test_empresa_cannot_manage_candidate_profile():
    user = User.objects.create_user(email='empresa@exemplo.com', password='senhaforte123', tipo='empresa')
    client = auth_client_for(user)

    response = client.get('/api/candidatos/perfil/')
    assert response.status_code == 403
