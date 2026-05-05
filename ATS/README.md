# ATS API

API REST para um fluxo de recrutamento e seleção (ATS), construída com Django, Django REST Framework e documentação OpenAPI via drf-spectacular.

## Funcionalidades implementadas

- Cadastro e autenticação de usuários (empresa e candidato)
- Endpoint de usuário autenticado (`me`)
- Gestão de perfil de candidato
- Escolaridade do candidato com opções padronizadas
- Experiências profissionais estruturadas (empresa, datas, responsabilidades e emprego atual)
- CRUD de vagas com regra de ownership (somente empresa dona da vaga pode alterar/excluir)
- Gestão de status da vaga (`aberta`, `encerrada`, `preenchida`)
- Listagem pública de vagas com busca por palavra-chave no título e descrição
- Criação de candidatura por candidato
- Regra de candidatura única por vaga
- Bloqueio de candidatura em vagas encerradas ou preenchidas
- Listagem de candidaturas do candidato
- Listagem de candidaturas por vaga (somente empresa dona da vaga)
- Pontuação de aderência de candidatos na gestão da vaga (0 a 2 pontos)
- Tag roxa `Hyped` para candidatos com 2/2 pontos de aderência
- Documentação Swagger e Redoc

## Tag Hyped

Na tela de gestão da vaga, cada candidato recebe pontuação:

- +1 ponto se a pretensão salarial estiver dentro da faixa da vaga
- +1 ponto se a escolaridade do candidato estiver no nível mínimo ou acima do exigido

Quando o candidato atinge **2/2 pontos**, ele recebe a tag **Hyped** (roxa), indicando aderência completa aos critérios de faixa salarial e escolaridade.

## Estrutura de apps

- `accounts`: autenticação, usuário e perfil de candidato
- `vagas`: gestão de vagas
- `candidaturas`: gestão de candidaturas
- `api`: configurações e rotas globais

## Requisitos

- Python 3.12+

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
task migrate
task run
