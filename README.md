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



## 📚 Recursos Adicionais

Documentação Streamlit
https://docs.streamlit.io/
Tutorial Pandas
https://pandas.pydata.org/docs/
Exemplos Plotly
https://plotly.com/python/

## 📝 Licença
Projeto acadêmico - livre para uso e modificação
