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

uninter-price-monitor/
├── app/
│ ├── main.py # Ponto de entrada da aplicação
│ ├── scraper.py # Coleta de preços via API
│ ├── database.py # Gerenciamento do SQLite
│ ├── notifier.py # Envio de alertas Telegram
│ └── scheduler.py # Agendamento de tarefas
├── data/ # Volume para persistência do banco
├── .env # Configurações sensíveis (não versionado)
├── .gitignore # Arquivos ignorados pelo Git
├── requirements.txt # Dependências Python
├── Dockerfile # Configuração do container
├── docker-compose.yml # Orquestração de serviços
└── README.md # Documentação
text

## Pré-requisitos

- Docker e Docker Compose instalados
- Token de bot do Telegram
- Chat ID do Telegram para recebimento das notificações

## Configuração

1. Clone o repositório:
   ```bash
   git clone https://github.com/regimarciio/uninter-price-monitor.git
   cd uninter-price-monitor
Crie o arquivo de configuração .env:

env
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
SCRAPE_INTERVAL_MINUTES=30
UNINTER_URL=https://www.uninter.com/graduacao-ead/tecnologia-em-ciencia-de-dados
Inicie a aplicação com Docker Compose:

bash
docker-compose up -d
Como obter as credenciais do Telegram
Crie um bot no Telegram através do @BotFather

Obtenha o token fornecido pelo BotFather

Envie uma mensagem para o seu bot

Acesse a URL para obter seu chat_id: https://api.telegram.org/botSEU_TOKEN/getUpdates

Monitoramento e Manutenção
bash
# Visualizar logs em tempo real
docker-compose logs -f

# Verificar status do container
docker-compose ps

# Reiniciar a aplicação
docker-compose restart

# Parar a aplicação
docker-compose down
Comandos Úteis
bash
# Ver histórico de preços
docker exec -it uninter-price-monitor sqlite3 /app/data/prices.db "SELECT datetime(timestamp, 'localtime'), price FROM prices ORDER BY timestamp DESC LIMIT 10;"

# Forçar uma verificação manual
docker exec -it uninter-price-monitor python -c "from main import PriceMonitor; PriceMonitor().check_price()"

# Testar scraper isoladamente
docker exec -it uninter-price-monitor python -c "from scraper import UninterScraper; s = UninterScraper(''); print(s.get_price())"
Comportamento do Sistema
A cada 30 minutos, o sistema consulta a API da UNINTER para obter o preço atual do curso

O valor obtido é comparado com o último registro no banco de dados

Em caso de alteração, uma notificação é enviada via Telegram

Todos os preços são registrados no banco SQLite para consulta histórica

Valores de Referência
Para a unidade de Joinville (utilizada como referência):

Mensalidade: R$ 201,10

Número de parcelas: 30

Opção de ingresso: VESTIBULAR ON-LINE

Contribuição
Contribuições são bem-vindas. Para contribuir:

Faça um fork do projeto

Crie uma branch para sua feature (git checkout -b feature/nova-funcionalidade)

Commit suas alterações (git commit -m 'Adiciona nova funcionalidade')

Push para a branch (git push origin feature/nova-funcionalidade)

Abra um Pull Request

