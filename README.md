Desenvolvido por: Robert Cristian dos Santos Domingues
Disciplina: Advanced Data for Big Data
Instituição: UniFECAF
Ano: 2025

# 📊 Painel E-Shop Brasil - Visualização de Dados

Painel administrativo para análise de dados de vendas com capacidade de manipulação de registros.

## 🚀 Tecnologias Utilizadas
- **Streamlit** (Framework para aplicações web com Python)
- **Pandas** (Manipulação de dados)
- **Plotly** (Visualizações interativas)
- **PyDeck** (Mapas geográficos)
- **MongoDB** (Opcional para grandes datasets)

## 📋 Pré-requisitos
- Conta no GitHub (para Codespaces)

## 🛠️ Instalação e Execução

### GitHub Codespaces
1. Acesse seu repositório no GitHub
2. Clique em "Code" > "Codespaces"
3. Crie um novo codespace
4. No terminal, execute:

docker-compose up --build


Usuário: adminfecaf

Senha: fecafadbd


eshop-analytics/

├── app.py               # Aplicação principal

├── requirements.txt     # Dependências

├── Dockerfile           # Configuração de container

├── docker-compose.yml   # Orquestração (com MongoDB)

└── data/                # Pasta para arquivos CSV (opcional)


## 💡 Funcionalidades Principais
#1. Upload de Dados
Suporte a arquivos CSV grandes (>10MB)

Validação automática das colunas necessárias

Pré-visualização dos dados

# 2. Dashboard Interativo
Métricas de vendas e clientes

Gráfico temporal de evolução de vendas

Visualização por cidade/região

# 3. Manipulação de Dados
Edição in-line de registros

Exclusão segura com confirmação

Adição de novos registros

# 4. Visualizações Avançadas
Mapa geográfico de distribuição

Gráficos interativos com filtros

Exportação de dados processados

## 📈 Exemplos de Análise
Identificar clientes mais valiosos

Analisar sazonalidade nas vendas

Comparar desempenho por região

Detectar produtos mais vendidos

## 🐛 Solução de Problemas
Problema	Solução
Erro no login	Verifique as credenciais no código
CSV não carrega	Confira se as colunas obrigatórias existem
Gráficos não atualizam	Recarregue a página (F5)
## 📚 Recursos Adicionais

Documentação Streamlit
https://docs.streamlit.io/
Tutorial Pandas
https://pandas.pydata.org/docs/
Exemplos Plotly
https://plotly.com/python/

## 📝 Licença
Projeto acadêmico - livre para uso e modificação
