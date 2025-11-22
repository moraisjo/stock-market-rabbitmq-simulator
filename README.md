# Projeto RabbitMQ - Bolsa de Valores

Este projeto demonstra o uso do RabbitMQ (via CloudAMQP) com um **producer** e um **consumer** em Python.

## Versão do Python
- Desenvolvido e testado com:
  - `Python 3.12.3`

## Ambiente virtual (venv)

### Criar o ambiente virtual
No diretório do projeto:

```bash
python3 -m venv .venv
```

### Ativar o ambiente virtual
Sempre que abrir um novo terminal e for trabalhar no projeto:

```bash
cd ~/Documents/puc/semestre2-2025/distribuidas-lab/rabbitMq
source .venv/bin/activate
```

Você saberá que o venv está ativo se o prompt aparecer com `(.venv)` no início.

### Instalar dependências dentro do venv

```bash
pip install --upgrade pip
pip install pika==1.1.0
```

## Variáveis de ambiente

O projeto **não** mantém credenciais no código. A URL de conexão com o RabbitMQ/CloudAMQP deve ser fornecida via variável de ambiente `AMQP_URL`, usada em `producer.py` e `consumer.py`.

### Definir `AMQP_URL`

No terminal (com o venv ativado ou não, tanto faz para o export):

```bash
export AMQP_URL="amqps://USUARIO:SENHA@HOST/VHOST"
```

Confirme que a variável foi definida:

```bash
echo "$AMQP_URL"
```

## Execução

1. Ativar o venv e garantir `AMQP_URL` exportado.
2. Em um terminal, iniciar o consumer:

   ```bash
   python consumer.py
   ```

3. Em outro terminal (também com venv ativo e `AMQP_URL` exportado), iniciar o producer:

   ```bash
   python producer.py
   ```

As mensagens do producer devem aparecer processadas no terminal do consumer.

## Rodar o Producer

Pré-requisitos: venv ativo e `AMQP_URL` definido.

```bash
source .venv/bin/activate
export AMQP_URL="amqps://USUARIO:SENHA@HOST/VHOST"   
python producer.py
```

Saída típica inicial:

```bash
[producer] Conectando
Mensagem enviada: bolsa.cotacoes.acoes.vale3 - {"acao": "VALE3", "valor": 77.84, "variacao": 0.42, "timestamp": 1763774643.6257765}
Mensagem enviada: bolsa.cotacoes.acoes.bbdc4 - {"acao": "BBDC4", "valor": 85.11, "variacao": 0.46, "timestamp": 1763774644.6265004}
Mensagem enviada: bolsa.negociacoes.venda.petr4 - {"acao": "PETR4", "quantidade": 840, "valor_total": 57724.7999, "tipo": "venda", "timestamp": 1763774646.628645}
...
```

## Rodar os Consumers

Atualmente existe um consumer parametrizado por tipo (cotações ou negociações). Por padrão o código inicia o de cotações.

```bash
source .venv/bin/activate
export AMQP_URL="amqps://USUARIO:SENHA@HOST/VHOST"
python consumer.py
```
Saída típica (cotações):

```bash
Iniciando consumer de COTAÇÕES...
Conectando
Consumer cotacoes aguardando mensagens...

Recebida mensagem com routing key: bolsa.cotacoes.acoes.vale3
Conteúdo: {"acao": "VALE3", "valor": 25.67, "variacao": 4.05, "timestamp": 1763773871.5680196}
Processando mensagem...
Cotação de VALE3: R$ 25.67 (variação: 4.05%)
ALERTA: VALE3 em alta expressiva!
Mensagem processada com sucesso!
```

Exemplo de alerta de queda:

```bash
Recebida mensagem com routing key: bolsa.cotacoes.acoes.bbdc4
Conteúdo: {"acao": "BBDC4", "valor": 68.84, "variacao": -2.55, "timestamp": 1763774645.6271808}
ALERTA: BBDC4 em queda expressiva!
```
