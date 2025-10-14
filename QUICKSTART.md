# 🚀 Quick Start Guide

## Setup Rápido (5 minutos)

### Windows

```bash
# 1. Navegue até a pasta do projeto
cd fipe_webapp

# 2. Execute o script de setup (automático)
setup.bat

# 3. Inicie a aplicação
venv\Scripts\activate
python app.py
```

### Linux/Mac

```bash
# 1. Navegue até a pasta do projeto
cd fipe_webapp

# 2. Torne o script executável e rode
chmod +x setup.sh
./setup.sh

# 3. Inicie a aplicação
source venv/bin/activate
python app.py
```

### Setup Manual

```bash
# 1. Crie ambiente virtual
python -m venv venv

# 2. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure o banco de dados
# Edite config.py e ajuste o caminho do DATABASE_URL

# 5. Execute
python app.py
```

## 📂 Arquivos do Projeto

Você precisa criar os seguintes arquivos na estrutura:

```
fipe_webapp/
├── app.py                          ✅ Aplicação Flask
├── config.py                       ✅ Configurações
├── webapp_database_models.py       ✅ Já existe (do scraper)
├── requirements.txt                ✅ Dependências
├── README.md                       ✅ Documentação
├── .gitignore                      ✅ Git ignore
├── setup.bat                       ✅ Setup Windows
├── setup.sh                        ✅ Setup Linux/Mac
│
├── templates/
│   └── index.html                  ✅ Página principal
│
└── static/
    ├── css/
    │   └── style.css              ✅ Estilos
    └── js/
        └── app.js                 ✅ JavaScript
```

## ⚙️ Configuração Mínima

### 1. Ajuste o caminho do banco de dados

Edite `config.py` linha 21:

```python
DATABASE_URL = 'sqlite:///C:/SEU/CAMINHO/AQUI/fipe_data.db'
```

### 2. (Opcional) Mude o veículo padrão

Edite `config.py` linhas 29-30:

```python
DEFAULT_BRAND = "Volkswagen"
DEFAULT_MODEL = "Gol"
```

## 🌐 Acessando a Aplicação

Após executar `python app.py`, abra seu navegador em:

```
http://127.0.0.1:5000
```

ou

```
http://localhost:5000
```

## ❓ Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'flask'"
**Solução:** Certifique-se de que o ambiente virtual está ativado e rode `pip install -r requirements.txt`

### Erro: "unable to open database file"
**Solução:** Ajuste o caminho do banco de dados em `config.py`

### Página não carrega
**Solução:** 
1. Verifique se o app.py está rodando sem erros
2. Certifique-se de acessar http://127.0.0.1:5000
3. Veja os logs no terminal onde rodou `python app.py`

### Gráfico não aparece
**Solução:**
1. Abra o Console do navegador (F12)
2. Veja se há erros JavaScript
3. Verifique se há dados no banco para o veículo selecionado

## 📱 Testando as APIs

Você pode testar as APIs diretamente:

```bash
# Listar marcas
curl http://127.0.0.1:5000/api/brands

# Listar modelos (exemplo: brand_id = 3)
curl http://127.0.0.1:5000/api/models/3

# Listar meses disponíveis
curl http://127.0.0.1:5000/api/months
```

## 🎯 Próximos Passos

1. ✅ Configure o projeto
2. ✅ Teste a aplicação
3. 📖 Leia o README.md completo
4. 🔧 Customize cores e estilos em `static/css/style.css`
5. 🚀 Faça deploy (Heroku, PythonAnywhere, Render, AWS, etc.)

## 💡 Dicas

- Use Ctrl+C no terminal para parar o servidor
- Modifique `static/css/style.css` para mudar cores e estilos
- Edite `templates/index.html` para mudar o layout
- Debug mode está ativo por padrão (auto-reload ao salvar)

## 📚 Recursos Úteis

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [Plotly JavaScript Documentation](https://plotly.com/javascript/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

**Pronto para começar? Execute `python app.py` e abra http://127.0.0.1:5000!** 🎉
