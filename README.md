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
1. Acesse o repositório:

https://github.com/robezin-TI/adbdcase

3. Clique em "Code" > "Download ZIP"
4. Baixe o arquivo e extraia
5. Crie um repositório com o nome que desejar
6. Clique em "File" > "Upload Files"
7. Selecione a pasta e os arquivos dentro dela
8. Clique em "Code" > "Create codespace on main"
9. Crie um novo codespace
10. No terminal, aguarde que as bibliotecas e aplicativos necessários sejam instalados (em torno de 2 a 3 minutos)
11. Ainda no terminal digite: "docker-compose up --build"
12. Quando finalizar um Popup irá aparecer escrito "Abrir no navegador"
13. Clique nele e o site abrirá
14. Caso contrario clique em: PORTAS > Abra o link ao lado da porta 8501
15. As credenciais foram fixadas na entrega do trabalho ou abaixo
16. Na aba upload: faça o upload do arquivo "relatorio_vendas" fixado junto com o trabalho
17. O arquivo suporta até 500_000 registros.


Usuário: adminfecaf

Senha: fecafadbd

eshop-analytics/

├── app.py               # Aplicação principal

├── requirements.txt     # Dependências

├── Dockerfile           # Configuração de container

└── docker-compose.yml   # Orquestração (com MongoDB)

### Documentação do Painel E-Shop Analytics 📊

## Visão Geral

Este é um painel administrativo completo para análise de dados de vendas, desenvolvido com:

Streamlit para a interface web

Pandas para processamento de dados

Plotly para visualizações gráficas

PyDeck para mapas interativos

MongoDB para armazenamento de dados (opcional)

## Funcionalidades Principais

# 1. Sistema de Autenticação 🔒
   
Login seguro com hash SHA-256

Credenciais padrão:

Usuário: adminfecaf

Senha: fecafadbd

Gerenciamento de sessão persistente

## 2. Upload de Dados 📤

#Dois modos de carregamento:

Combinar múltiplos arquivos: Ideal para consolidar dados de diferentes períodos

Acumular dados: Adiciona novos dados aos já existentes

Validação automática da estrutura dos arquivos CSV

Suporte a arquivos grandes (processamento em chunks)

Limpeza segura dos dados carregados

## 3. Visualização Completa 🔍
Tabela interativa com paginação

Filtros avançados por:

Cliente

Cidade

Item/produto

Estatísticas gerais automáticas

Resumo por cliente com:

Total gasto

Última compra

Quantidade de itens comprados

## 4. Análise de Clientes 👥
Ranking de clientes por valor gasto

Filtros por:

Cidade

Valor mínimo gasto

Visualizações gráficas:

Top 10 clientes (gráfico de barras)

Distribuição por cidade (gráfico de pizza)

## 5. Logística e Distribuição 🚚
Mapa interativo das vendas por região

Métricas-chave:

Total de vendas

Itens vendidos

Cobertura geográfica

Gráfico de barras por região

## 6. Dashboard Geral 📊

Visão consolidada com KPIs:

Total de clientes

Faturamento total

Cobertura geográfica

Gráfico de evolução temporal das vendas

## Estrutura Técnica

# Arquitetura

graph TD
    A[Interface Streamlit] --> B[Processamento Pandas]
    B --> C[Visualização Plotly/PyDeck]
    A --> D[(MongoDB - Opcional)]

# Dependências

Listadas no requirements.txt:

streamlit>=1.22.0

pandas>=1.5.3

plotly-express>=0.4.1

pydeck>=0.8.0

pymongo>=4.3.3

numpy>=1.23.5

## Como Executar

# 1. Via Docker (Recomendado)

docker-compose up -d --build

# 2. Localmente

pip install -r requirements.txt
streamlit run app.py

## Estrutura Esperada do CSV

Os arquivos CSV devem conter estas colunas:

ID Cliente

Nome do Cliente

Cidade

Item

Quantidade

Preço Unitário (R$)

Preço Total (R$)

Data (opcional)

## 📚 Recursos Adicionais

Documentação Streamlit

https://docs.streamlit.io/

Tutorial Pandas

https://pandas.pydata.org/docs/

Exemplos Plotly

https://plotly.com/python/

## 📝 Licença
Projeto acadêmico - livre para uso e modificação
