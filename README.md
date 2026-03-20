# UNINTER Course Price Monitor

Sistema automatizado para monitoramento de preços do curso de Tecnologia em Ciência de Dados EAD da UNINTER. A aplicação coleta o valor da mensalidade via API, registra histórico em banco de dados SQLite e envia notificações via Telegram quando há alteração no preço.

## Funcionalidades

- Coleta automática do preço do curso através da API oficial da UNINTER
- Registro histórico de preços em banco de dados SQLite
- Notificações em tempo real via Telegram apenas quando o preço é alterado
- Agendamento de verificações a cada 30 minutos
- Execução contínua em container Docker
- Persistência de dados através de volume Docker

## Tecnologias Utilizadas

- Python 3.11
- SQLite para armazenamento local
- Selenium para automação de navegação
- Telegram Bot API para notificações
- Docker e Docker Compose para containerização
- APScheduler para agendamento de tarefas

## Estrutura do Projeto


