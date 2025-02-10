# Workflow de Coleta e Análise de Dados de Ações com Prefect

Este repositório contém um workflow automatizado desenvolvido com Prefect para coletar dados financeiros de ações, processá-los e armazená-los em um bucket S3, gerando relatórios diários.

## Funcionalidades

- Coleta de dados de ações via API do Yahoo Finance.
- Processamento dos dados com cálculo de indicadores financeiros básicos.
- Armazenamento dos dados localmente e no Amazon S3.
- Geração de links para acesso aos arquivos armazenados.
- Agendamento automático do workflow via Prefect.

## Tecnologias Utilizadas

- **Python**: Linguagem principal.
- **Prefect**: Framework de orquestração de workflows.
- **Yahoo Finance (yfinance)**: Coleta de dados de ações.
- **AWS S3**: Armazenamento na nuvem.
- **Pandas**: Manipulação e análise de dados.

## Estrutura do Código

- `stock_workflow()`: Função principal do workflow.
- `download_and_partition()`: Coleta dados de ações e os separa por data.
- `save_local_partitions()`: Armazena os dados localmente em um diretório estruturado.
- `upload_partitions_to_s3()`: Faz upload dos arquivos para um bucket S3.
- `upload_to_s3()`: Função auxiliar para realizar uploads ao S3.
- `get_date_ranges()`: Define o período de coleta de dados.

## Como Executar

1. Clone este repositório:
   ```sh
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```
2. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```
3. Configure as variáveis de ambiente do AWS S3 e Prefect.
4. Execute o workflow:
   ```sh
   python projeto.py
   ```

## Agendamento Automático

O workflow está configurado para rodar automaticamente via Prefect Cloud ou um agente local. O agendamento pode ser ajustado no código conforme necessário.

## Dificuldades e Soluções

- **Erro no download de ações**: Algumas requisições falhavam devido a problemas na API. A solução foi adicionar tentativas de reexecução com `retries` e `retry_delay_seconds`.
- **Falhas no upload para o S3**: Erros relacionados a credenciais foram resolvidos garantindo a correta configuração das credenciais do AWS no Prefect.

## Licença

Este projeto está sob a licença MIT.

