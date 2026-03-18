# FIPE Price Tracker - Histórico de Preços da Tabela FIPE

Uma aplicação web para visualizar e comparar o histórico de preços de veículos da Tabela FIPE com gráficos interativos.

## Banco de Dados

O banco de dados completo com os dados históricos da Tabela FIPE (atualizado em março/2026) está disponível para download:

**[Download do banco de dados (Google Drive)](https://drive.google.com/file/d/11fiyjqPlqro020rtuEYQN7UMfCeHF5UT/view?usp=drive_link)**

Após o download, coloque o arquivo `fipe_data.db` na pasta `data/` do projeto.

Consulte [docs/database_schema.md](docs/database_schema.md) para detalhes sobre a estrutura do banco.

## Funcionalidades

**Análise e Visualização:**
- Seleção de veículos com dropdowns em cascata (Marca, Modelo, Ano)
- Filtragem inteligente - mostra apenas veículos disponíveis na Tabela FIPE mais recente
- Filtragem bidirecional - selecione modelo ou ano primeiro, o outro se ajusta automaticamente
- Gráfico interativo com Plotly mostrando evolução de preços
- Comparação de até 5 veículos no mesmo gráfico com cores distintas
- Seleção de período (mês inicial e final)
- Estatísticas automáticas por veículo (preço atual, mínimo, máximo, variação percentual)
- Indicadores econômicos (IPCA e CDI) integrados ao gráfico
- Visualização em preços absolutos ou indexada (Base 100)
- Análise de depreciação por marca e ano

**Interface e Usabilidade:**
- Modo escuro/claro com persistência de preferência
- Interface moderna com Bootstrap 5
- Atualizações dinâmicas sem recarregar a página
- Design responsivo para mobile e desktop

**Segurança e Desempenho:**
- Content Security Policy (CSP) com execução nonce-based
- Rate limiting em todos os endpoints
- Logging em produção com rotação automática
- Health check endpoint para monitoramento
- Validação de schema do banco na inicialização

**API Pública:**
- API REST com documentação completa em `/api/docs`
- 9 endpoints para consulta de preços, comparação e análise
- Sem necessidade de autenticação

## Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Banco de dados SQLite com dados da Tabela FIPE (veja seção acima)

### Passo 1: Clone o repositório

```bash
git clone https://github.com/seu-usuario/historico_fipe_webapp.git
cd historico_fipe_webapp
```

### Passo 2: Instale as dependências

```bash
# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### Passo 3: Configure as variáveis de ambiente

```bash
# Copie o template
cp .env.example .env

# Edite .env e ajuste conforme necessário
```

O banco de dados SQLite é detectado automaticamente na pasta `data/fipe_data.db`. Se você colocou o arquivo em outro local, ajuste a variável `DATABASE_URL` no `.env`.

### Passo 4: Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://127.0.0.1:5000`

## Como Usar

1. **Selecione o veículo:** Escolha marca, modelo e ano nos dropdowns
2. **Defina o período:** Selecione mês inicial e final
3. **Adicione à comparação:** Clique em "Adicionar à Comparação" (até 5 veículos)
4. **Visualize:** Clique em "Atualizar Gráfico" para ver a evolução dos preços
5. **Explore:** Use zoom, hover e os controles do Plotly para interagir com o gráfico

## Documentação da API

A documentação completa da API está disponível em `/api/docs` quando a aplicação está rodando. A API é pública e não requer autenticação.

**Endpoints disponíveis:**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/brands` | GET | Lista de marcas |
| `/api/vehicle-options/<brand_id>` | GET | Modelos e anos de uma marca |
| `/api/months` | GET | Meses de referência disponíveis |
| `/api/default-car` | GET | Veículo padrão |
| `/api/compare-vehicles` | POST | Histórico de preços para comparação |
| `/api/price` | POST | Consulta de preço pontual |
| `/api/economic-indicators` | POST | Indicadores IPCA e CDI |
| `/api/depreciation-analysis` | GET | Análise de depreciação de mercado |
| `/health` | GET | Status do serviço |

## Configuração Avançada

### Variáveis de Ambiente

Todas as configurações são gerenciadas via arquivo `.env`:

| Variável | Descrição |
|----------|-----------|
| `FLASK_ENV` | Ambiente (`development` ou `production`) |
| `DATABASE_URL` | String de conexão do banco de dados |
| `SECRET_KEY` | Chave secreta para sessões Flask |
| `DEFAULT_BRAND` | Marca padrão ao carregar a página |
| `DEFAULT_MODEL` | Modelo padrão ao carregar a página |
| `GA_MEASUREMENT_ID` | ID do Google Analytics 4 (opcional) |

Para gerar uma chave secreta:
```bash
python generate_secret_key.py
```

### Usando PostgreSQL (Produção)

```bash
pip install psycopg2-binary
```

Configure no `.env`:
```
DATABASE_URL=postgresql://usuario:senha@localhost/fipe_db
FLASK_ENV=production
```

## Estrutura do Projeto

```
historico_fipe_webapp/
├── app.py                          # Aplicação principal Flask
├── config.py                       # Configurações (usa .env)
├── webapp_database_models.py       # Modelos do banco de dados
├── generate_secret_key.py          # Gerador de chaves seguras
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de configuração
│
├── templates/
│   ├── index.html                  # Página principal
│   └── api_docs.html              # Documentação da API
│
├── static/
│   ├── css/style.css              # Estilos customizados
│   └── js/app.js                  # JavaScript frontend
│
└── docs/
    └── database_schema.md         # Estrutura do banco de dados
```

## Tecnologias

- **Backend:** Flask 3.0, SQLAlchemy 2.0, Python 3.8+
- **Frontend:** Bootstrap 5.3, Plotly.js 2.26, JavaScript vanilla
- **Banco de Dados:** SQLite 3 (desenvolvimento), PostgreSQL (produção)

## Solução de Problemas

**"No module named 'flask'"** - Execute `pip install -r requirements.txt`

**"Unable to open database file"** - Verifique se o arquivo `fipe_data.db` está na pasta `data/` e se o caminho em `.env` está correto.

**Gráfico não carrega** - Abra o Console do Navegador (F12) para ver erros. Verifique se o banco tem dados para o veículo selecionado.

## Melhorias Futuras

- Sugestões de veículos similares baseadas em faixa de preço e segmento
- Dashboard de tendências de mercado com ranking de marcas
- Detector de anomalias para identificar valorizações atípicas
- Scatter plots e gráficos de distribuição
- Tracker de carros clássicos (veículos com 20+ anos em valorização)
- Busca avançada por código FIPE com autocomplete
- Cache com Redis para otimizar performance

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

Desenvolvido com Flask + Python
