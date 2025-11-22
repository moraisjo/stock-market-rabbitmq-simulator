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

## Execução (resumo)

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

