# FIPE Price Tracker - Flask Webapp

Uma aplicação web para visualizar o histórico de preços de veículos da Tabela FIPE.

> **⚠️ IMPORTANTE:** Este projeto é apenas a interface web (webapp) e **requer um banco de dados separado** com os dados históricos da Tabela FIPE. O banco de dados e os dados **NÃO estão incluídos** neste repositório. Você precisará de um scraper ou fonte de dados separada para popular o banco antes de usar esta aplicação.

## ✨ Novidades Recentes

### Versão Atual (Outubro 2025)

**🔒 Melhorias de Segurança**
- **Content Security Policy (CSP)** implementada com nonce-based script execution para prevenir XSS
- **Referrer-Policy** configurada para prevenir vazamento de informações
- **Rate limiting** em todos os endpoints da API
- **Logging em produção** com rotação automática (10MB × 10 arquivos)
- **Validação de schema** do banco de dados na inicialização
- **Health check endpoint** (`/health`) para monitoramento e load balancers

**🔄 Comparação de Múltiplos Veículos**
- Compare até 5 veículos no mesmo gráfico
- Cores distintas para cada veículo
- Estatísticas individuais por veículo
- Indicadores econômicos (IPCA e CDI) integrados

**📉 Análise de Depreciação**
- Estatísticas de mercado por marca e ano
- Visualização de tendências de depreciação
- Segunda aba dedicada à análise de depreciação

**🌙 Modo Escuro Completo**
- Toggle entre temas claro/escuro com um clique
- Persistência de preferência no navegador (localStorage)
- Detecção automática de preferência do sistema operacional
- Gráficos Plotly adaptam cores automaticamente ao tema
- Transições suaves entre temas

**🔄 Filtragem Inteligente por Mês Mais Recente**
- Dropdowns mostram apenas veículos disponíveis na Tabela FIPE mais atual
- Elimina modelos descontinuados automaticamente
- Exemplo: Porsche 2005 agora mostra 17 modelos (eram 20 com modelos descontinuados)
- Garante que você veja apenas veículos com dados atuais

**🔀 Filtragem Bidirecional Aprimorada**
- Selecione modelo OU ano primeiro - o outro se ajusta automaticamente
- Navegação mais intuitiva e flexível
- Reduz cliques desnecessários
- API otimizada com `/api/vehicle-options` que retorna dados em uma única chamada

## 📋 Funcionalidades

**Análise e Visualização:**
- ✅ Seleção de veículos com dropdowns em cascata (Marca → Modelo → Ano)
- 🔄 **Filtragem inteligente** - Mostra apenas veículos disponíveis na Tabela FIPE mais recente
- 🔀 **Filtragem bidirecional** - Selecione modelo ou ano primeiro, o outro se ajusta automaticamente
- 📊 Gráfico interativo com Plotly mostrando evolução de preços
- 🔄 **Comparação de até 5 veículos** no mesmo gráfico com cores distintas
- 📅 Seleção de período (mês inicial e final)
- 📈 **Estatísticas automáticas** por veículo (preço atual, mínimo, máximo, variação percentual)
- 💹 **Indicadores econômicos** (IPCA e CDI) integrados ao gráfico para contexto
- 📊 Visualização em preços absolutos ou **indexada (Base 100)** para comparar variações
- 📉 **Análise de depreciação** - Estatísticas de mercado por marca e ano

**Interface e Usabilidade:**
- 🌙 **Modo escuro/claro** - Toggle entre temas com persistência de preferência
- 🎨 Interface moderna com Bootstrap 5 e design premium
- 🔄 Atualizações dinâmicas sem recarregar a página
- 📱 Design responsivo para mobile e desktop

**Segurança e Desempenho:**
- 🔐 **Autenticação com API keys** para proteção dos endpoints
- 🛡️ **Content Security Policy (CSP)** com execução nonce-based para prevenir XSS
- 🚦 **Rate limiting** para prevenir abuso da API
- 📝 **Logging em produção** com rotação automática
- 🏥 **Health check endpoint** para monitoramento
- ✅ **Validação de schema** do banco na inicialização

**Infraestrutura:**
- 💾 Suporte para SQLite (desenvolvimento) e PostgreSQL (produção)
- 🔄 Sistema de configuração via variáveis de ambiente (.env)

## 🗂️ Estrutura do Projeto

```
historico_fipe_webapp/
│
├── app.py                          # Aplicação principal Flask
├── config.py                       # Configurações (usa .env)
├── webapp_database_models.py       # Modelos do banco de dados
├── generate_secret_key.py          # Gerador de chaves seguras
├── requirements.txt                # Dependências Python
├── .env                            # Variáveis de ambiente (não commitado)
├── .env.example                    # Template de configuração
│
├── templates/                      # Templates HTML
│   └── index.html                  # Página principal
│
├── static/                         # Arquivos estáticos
│   ├── css/
│   │   └── style.css              # Estilos customizados
│   └── js/
│       └── app.js                 # JavaScript frontend
│
└── docs/                           # 📚 Documentação
    ├── database_schema.md         # Estrutura do banco de dados
    └── ENV_SETUP.md               # Guia de configuração
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- **Banco de dados SQLite ou PostgreSQL com dados históricos da Tabela FIPE**
  - ⚠️ O banco de dados **NÃO está incluído** neste projeto
  - Você precisa ter um `fipe_data.db` populado com dados antes de usar esta aplicação
  - Use um scraper separado para coletar dados da Tabela FIPE
  - Consulte [docs/database_schema.md](docs/database_schema.md) para ver a estrutura necessária

### Passo 1: Clone ou crie o projeto

```bash
# Crie a estrutura de pastas
mkdir fipe_webapp
cd fipe_webapp
mkdir templates static
mkdir static/css static/js
```

### Passo 2: Instale as dependências

```bash
# Crie um ambiente virtual (recomendado)
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### Passo 3: Configure as variáveis de ambiente

Copie o arquivo de exemplo e edite com suas configurações:

```bash
# Copie o template
cp .env.example .env

# Edite .env e ajuste o caminho do banco de dados
# DATABASE_URL=sqlite:///C:/Users/seu_usuario/caminho/para/fipe_data.db
```

**Veja [docs/ENV_SETUP.md](docs/ENV_SETUP.md) para guia completo de configuração.**

### Passo 4: Execute a aplicação

```bash
python app.py
```

A aplicação estará disponível em: `http://127.0.0.1:5000`

## ⚙️ Configuração Avançada

### Usando PostgreSQL (Produção)

1. Instale o driver PostgreSQL:
```bash
pip install psycopg2-binary
```

2. Configure a variável de ambiente `DATABASE_URL`:
```bash
# Windows
set DATABASE_URL=postgresql://usuario:senha@localhost/fipe_db

# Linux/Mac
export DATABASE_URL=postgresql://usuario:senha@localhost/fipe_db
```

### Variáveis de Ambiente

Todas as configurações são gerenciadas via arquivo `.env`. Variáveis disponíveis:

- `FLASK_ENV` - Ambiente (`development` ou `production`)
- `DATABASE_URL` - String de conexão do banco de dados
- `SECRET_KEY` - Chave secreta para sessões Flask
- `API_KEY` - Chave da aplicação (usada pelo frontend para autenticação)
- `API_KEYS_ALLOWED` - Lista de chaves válidas separadas por vírgula (deve incluir API_KEY)
- `DEFAULT_BRAND` - Marca padrão ao carregar a página
- `DEFAULT_MODEL` - Modelo padrão ao carregar a página
- `SQLALCHEMY_ECHO` - Mostrar queries SQL (`True` ou `False`)

Para gerar chaves seguras:
```bash
# Gerar SECRET_KEY
python generate_secret_key.py

# Gerar API_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**📖 Documentação completa:** [docs/ENV_SETUP.md](docs/ENV_SETUP.md)

## 🎯 Como Usar

1. **Selecione o veículo:**
   - Escolha a marca no primeiro dropdown
   - O dropdown de modelos será atualizado automaticamente
   - Selecione o modelo desejado
   - Escolha o ano e tipo de combustível

2. **Defina o período:**
   - Selecione o mês inicial
   - Selecione o mês final
   - O período padrão mostra todos os meses disponíveis

3. **Visualize o gráfico:**
   - Clique em "Atualizar Gráfico"
   - O gráfico será carregado com os dados do período selecionado
   - Veja as estatísticas abaixo do gráfico

4. **Interaja com o gráfico:**
   - Passe o mouse sobre os pontos para ver detalhes
   - Use os controles do Plotly para zoom e navegação
   - Baixe o gráfico como imagem usando o ícone da câmera

## 🔧 Personalizando o Veículo Padrão

Edite o arquivo `.env` para mudar o veículo que aparece ao carregar a página:

```bash
DEFAULT_BRAND=Volkswagen
DEFAULT_MODEL=Gol  # Busca modelos contendo "Gol"
```

## 📡 Endpoints da API

A aplicação expõe 11 endpoints JSON (requerem autenticação via header `X-API-Key`, exceto `/` e `/health`):

**Dados de Veículos:**
- `GET /api/brands` - Lista marcas disponíveis na Tabela FIPE mais recente
- `GET /api/vehicle-options/<brand_id>` - Retorna modelos e anos com mapeamento bidirecional para filtragem inteligente
- `GET /api/months` - Lista todos os meses disponíveis
- `GET /api/default-car` - Retorna o veículo padrão (com nomes e IDs)

**Preços e Histórico:**
- `POST /api/chart-data` - Retorna dados para o gráfico de um único veículo (endpoint legado, ainda funciona)
- `POST /api/compare-vehicles` - Retorna dados de múltiplos veículos para comparação (até 5 veículos)
- `POST /api/price` - Retorna preço de um veículo específico em um mês específico

**Análise Econômica e de Mercado:**
- `POST /api/economic-indicators` - Retorna indicadores econômicos (IPCA e CDI) para períodos
- `POST /api/depreciation-analysis` - Retorna estatísticas de depreciação por marca/ano

**Sistema:**
- `GET /health` - Endpoint de saúde para monitoramento e load balancers
- `GET /` - Página principal (sem autenticação)

### Autenticação

Todos os endpoints da API requerem uma chave de API no header:

```bash
curl -H "X-API-Key: sua-chave-aqui" http://127.0.0.1:5000/api/brands
```

O frontend da aplicação automaticamente inclui a chave configurada em `API_KEY`. Para clientes externos, adicione suas chaves em `API_KEYS_ALLOWED` no arquivo `.env`.

## 🔒 Segurança

O aplicativo implementa múltiplas camadas de segurança:

**Content Security Policy (CSP):**
- Execução de scripts baseada em nonce para prevenir ataques XSS
- Scripts externos permitidos apenas de CDNs confiáveis
- Proteção contra injeção de código malicioso

**Autenticação com API Keys:**
- Todos os endpoints da API (exceto `/` e `/health`) requerem autenticação
- Chave incluída automaticamente no header `X-API-Key` pelo frontend
- Suporte para múltiplas chaves para clientes externos

**Rate Limiting:**
- 200 requisições por dia, 50 por hora por IP (padrão)
- Endpoints específicos com limites ajustados para uso normal
- Retorna HTTP 429 quando limite é excedido

**Logging em Produção:**
- Rotação automática de logs (10MB por arquivo, 10 backups)
- Logs de acesso com prefixo de chave, endpoint e IP
- Logs de tentativas de acesso inválidas

**Validação de Schema:**
- Verifica integridade do banco de dados na inicialização
- Aplicação recusa iniciar se schema estiver inválido

**Health Check:**
- Endpoint `/health` para monitoramento e load balancers
- Verifica conectividade com banco de dados
- Retorna status detalhado em JSON

**Referrer-Policy:**
- Previne vazamento de informações em headers HTTP
- Apenas origem (não URL completa) enviada para sites externos

## 🐛 Solução de Problemas

### Erro: "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Erro: "Unable to open database file"
- **Verifique se você tem um banco de dados FIPE** - este projeto NÃO inclui os dados
- Verifique se o caminho do banco em `.env` (variável `DATABASE_URL`) está correto
- Certifique-se de que o banco de dados foi populado com dados da Tabela FIPE
- Verifique se você tem permissão de leitura no arquivo
- Consulte [docs/database_schema.md](docs/database_schema.md) para a estrutura esperada
- Veja o guia de configuração: [docs/ENV_SETUP.md](docs/ENV_SETUP.md)

### Gráfico não carrega
- Abra o Console do Navegador (F12) para ver erros
- Verifique se o banco de dados tem dados para o veículo selecionado
- Confirme que a API está respondendo (teste os endpoints diretamente)

### Dropdowns não atualizam
- Verifique o Console do Navegador para erros JavaScript
- Confirme que os arquivos em `static/js/` estão sendo carregados

### Erro: "API key required"
- Configure `API_KEY` e `API_KEYS_ALLOWED` no arquivo `.env`
- Certifique-se de que `API_KEY` está incluído em `API_KEYS_ALLOWED`
- Se estiver testando, pode deixar vazio para permitir acesso em modo desenvolvimento

## 📚 Tecnologias Utilizadas

- **Backend:**
  - Flask 3.0 - Framework web Python
  - SQLAlchemy 2.0 - ORM para banco de dados
  - Python 3.8+

- **Frontend:**
  - Bootstrap 5.3 - Framework CSS
  - Plotly.js 2.26 - Biblioteca de gráficos interativos
  - Vanilla JavaScript - Sem dependências adicionais

- **Banco de Dados:**
  - SQLite 3 (desenvolvimento)
  - PostgreSQL (produção - opcional)

## 🔜 Melhorias Futuras

### 🎯 Prioridades (Quick Wins)
- [ ] **Sugestões de veículos similares** - Ajudar a descobrir alternativas

### 📊 Análise de Dados & Insights
- [ ] **Dashboard de tendências de mercado** - Quais marcas/segmentos estão valorizando
- [ ] **Análise de depreciação** - Taxa média por marca/modelo/ano
- [ ] **Detector de anomalias** - Carros que estão valorizando inesperadamente
- [ ] **Previsão de valores** - Regressão linear para estimar preços futuros
- [ ] **Análise sazonal** - Melhores/piores meses para comprar/vender
- [ ] **Comparação "Real vs Nominal"** - Valorização real ajustada por inflação

### 🔍 Ferramentas de Comparação
- [ ] **Análise de segmentos** - Comparar categorias inteiras (SUVs, sedãs, hatches)
- [ ] **Prêmio de marca** - Quanto a mais cada marca cobra vs média do mercado
- [ ] **Comparação por tipo de combustível** - Evolução de preços gasolina vs flex vs diesel
- [ ] **Veículos concorrentes** - Sugestões automáticas baseadas em faixa de preço/categoria

### 💡 Visualizações Avançadas
- [ ] **Scatter plots** - Preço vs idade, correlações diversas
- [ ] **Heatmaps** - Melhores meses para comprar por marca/modelo
- [ ] **Gráficos de distribuição** - Faixas de preço por categoria
- [ ] **Anotações em gráficos** - Marcar eventos importantes (crise dos chips, etc.)
- [ ] **Tabela de dados** - Exibir dados tabulares abaixo dos gráficos

### 🎯 Recursos para Usuários
- [ ] **Watchlist & Alertas** - Salvar veículos favoritos e receber notificações
- [ ] **Portfolio tracker** - Acompanhar valor dos seus veículos ao longo do tempo
- [ ] **Calculadora de financiamento** - Com depreciação integrada
- [ ] **Otimizador "quando vender"** - Sugerir melhor momento de venda
- [ ] **Custo total de propriedade** - Estimativa incluindo depreciação

### 🚗 Para Entusiastas de Carros
- [ ] **Tracker de carros clássicos** - Seção especial para veículos valorizando
- [ ] **Potencial de investimento** - Score para carros entrando em "classic territory"
- [ ] **Integração com dados de performance** - HP, 0-100, consumo vs preço
- [ ] **Análise preço por HP** - Value proposition comparisons
- [ ] **Impacto de quilometragem** - Como km rodados afetam depreciação

### 🎨 UI/UX
- [ ] **Filtros rápidos** - Por combustível, faixa de preço, ano, segmento
- [ ] **Otimização mobile** - Touch gestures, swipe entre veículos
- [ ] **Busca avançada** - Por código FIPE, busca full-text
- [ ] **Pesquisas salvas** - Guardar combinações de filtros
- [ ] **Modo comparação melhorado** - Drag & drop de veículos

### 🔧 Melhorias Técnicas
- [ ] **Cache de dados** - Redis/Memcached para melhor performance
- [ ] **Indicadores de atualização** - Mostrar quando dados foram atualizados
- [ ] **Auto-refresh** - Opção de atualização automática
- [ ] **Autenticação de usuários** - Sistema de contas
- [ ] **API REST completa** - Documentação Swagger/OpenAPI

### 👥 Features Comunitárias
- [ ] **Comentários e notas** - Usuários podem adicionar observações sobre veículos
- [ ] **Sistema de votação** - "Melhor custo-benefício" votado pela comunidade
- [ ] **Compartilhar análises** - Links compartilháveis de comparações
- [ ] **Exportar relatórios PDF** - Gerar PDFs profissionais com análises

## 📚 Documentação Adicional

Este projeto inclui documentação detalhada:

- **[docs/database_schema.md](docs/database_schema.md)** - Estrutura completa do banco de dados com ERD
- **[docs/ENV_SETUP.md](docs/ENV_SETUP.md)** - Guia completo de configuração de variáveis de ambiente
- **[QUICKSTART.md](QUICKSTART.md)** - Guia rápido de instalação (5 minutos)
- **[CLAUDE.md](CLAUDE.md)** - Guia técnico para desenvolvedores e IA assistentes

### Notas para Iniciantes

O código está comentado para ajudar iniciantes em Python/Flask:
- **app.py** - Explicações sobre cada rota e função
- **static/js/app.js** - Como o JavaScript interage com a API
- **webapp_database_models.py** - Documentação dos modelos de dados

Não hesite em explorar o código e fazer modificações!

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Contribuindo

Sugestões e melhorias são bem-vindas! 

---

Desenvolvido com ❤️ usando Flask e Bootstrap 5
