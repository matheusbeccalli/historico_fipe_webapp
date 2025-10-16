# FIPE Price Tracker - Flask Webapp

Uma aplicação web para visualizar o histórico de preços de veículos da Tabela FIPE.

## 📋 Funcionalidades

- ✅ Seleção de veículos com dropdowns em cascata (Marca → Modelo → Ano)
- 📊 Gráfico interativo com Plotly mostrando evolução de preços
- 📅 Seleção de período (mês inicial e final)
- 📈 Estatísticas automáticas (preço atual, mínimo, máximo, variação)
- 🎨 Interface moderna com Bootstrap 5
- 🔄 Atualizações dinâmicas sem recarregar a página
- 💾 Suporte para SQLite (desenvolvimento) e PostgreSQL (produção)

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
- Banco de dados SQLite ou Postgre com dados FIPE (fipe_data.db)

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
- `DEFAULT_BRAND` - Marca padrão ao carregar a página
- `DEFAULT_MODEL` - Modelo padrão ao carregar a página
- `SQLALCHEMY_ECHO` - Mostrar queries SQL (`True` ou `False`)

Para gerar uma chave secreta segura:
```bash
python generate_secret_key.py
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

A aplicação expõe os seguintes endpoints JSON:

- `GET /api/brands` - Lista todas as marcas
- `GET /api/models/<brand_id>` - Lista modelos de uma marca
- `GET /api/years/<model_id>` - Lista anos de um modelo
- `GET /api/months` - Lista todos os meses disponíveis
- `POST /api/chart-data` - Retorna dados para o gráfico (histórico completo)
- `POST /api/price` - Retorna preço de um veículo específico em um mês específico
- `GET /api/default-car` - Retorna o veículo padrão

## 🐛 Solução de Problemas

### Erro: "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Erro: "Unable to open database file"
- Verifique se o caminho do banco em `.env` (variável `DATABASE_URL`) está correto
- Verifique se você tem permissão de leitura no arquivo
- Veja o guia de configuração: [docs/ENV_SETUP.md](docs/ENV_SETUP.md)

### Gráfico não carrega
- Abra o Console do Navegador (F12) para ver erros
- Verifique se o banco de dados tem dados para o veículo selecionado
- Confirme que a API está respondendo (teste os endpoints diretamente)

### Dropdowns não atualizam
- Verifique o Console do Navegador para erros JavaScript
- Confirme que os arquivos em `static/js/` estão sendo carregados

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

Algumas ideias para expandir o projeto:

- [ ] Comparação de múltiplos veículos no mesmo gráfico
- [ ] Tabela de dados abaixo do gráfico
- [ ] Exportar dados para CSV/Excel
- [ ] Filtros adicionais (marca, faixa de preço, etc.)
- [ ] Sistema de favoritos
- [ ] Gráficos adicionais (barras, pizza, etc.)
- [ ] Cache de dados para melhor performance
- [ ] Autenticação de usuários
- [ ] API REST completa

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

Este projeto é livre para uso educacional e pessoal.

## 🤝 Contribuindo

Sugestões e melhorias são bem-vindas! 

---

Desenvolvido com ❤️ usando Flask e Bootstrap 5
