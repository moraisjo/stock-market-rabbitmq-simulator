import os
import pika
import json
import time
import random
from urllib.parse import urlparse

def conectar_rabbitmq(amqp_url):
    """Estabelece conexão com o RabbitMQ e garante exchange (idempotente)."""
    if not amqp_url:
        raise RuntimeError("AMQP_URL não definido. Exporte: export AMQP_URL='amqps://usuario:senha@host/vhost'")

    parsed = urlparse(amqp_url)
    user = parsed.username
    vhost = parsed.path.lstrip('/') or '/'
    host = parsed.hostname
    print(f"[producer] Conectando -> host={host} vhost={vhost} user={user} ssl={'amqps' in amqp_url}")

    params = pika.URLParameters(amqp_url)
    params.socket_timeout = 5
    try:
        connection = pika.BlockingConnection(params)
    except pika.exceptions.ProbableAuthenticationError as e:
        raise RuntimeError("[producer] Falha de autenticação (403). Confirme usuário, senha, vhost e URL: " + amqp_url) from e
    channel = connection.channel()

    def ensure_exchange(ch):
        """Garante exchange 'bolsa'. Trata conflito 406 devolvendo instruções."""
        try:
            ch.exchange_declare(exchange='bolsa', passive=True)
            return ch  # já existe com algum parâmetro
        except pika.exceptions.ChannelClosedByBroker as e:
            if connection.is_open:
                ch = connection.channel()  # reabrir canal
            if 'NOT_FOUND' in str(e):
                ch.exchange_declare(exchange='bolsa', exchange_type='topic', durable=True, auto_delete=False)
                return ch
            if 'PRECONDITION_FAILED' in str(e):
                print("[producer] Exchange 'bolsa' existe com outros argumentos. Tentando deletar e recriar...")
                try:
                    ch.exchange_delete(exchange='bolsa')
                    ch.exchange_declare(exchange='bolsa', exchange_type='topic', durable=True, auto_delete=False)
                    print("[producer] Exchange recriado com sucesso.")
                    return ch
                except Exception as del_err:
                    raise RuntimeError("Não foi possível ajustar exchange automaticamente. Delete 'bolsa' manualmente (type=topic durable=true auto_delete=false). Erro interno: " + str(del_err)) from del_err
            raise

    channel = ensure_exchange(channel)
    return connection, channel

def publicar_mensagem(channel, routing_key, mensagem):
    """Publica uma mensagem no exchange com a routing key especificada."""
    channel.basic_publish(
        exchange='bolsa',
        routing_key=routing_key,
        body=json.dumps(mensagem),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Mensagem persistente
            content_type='application/json'
        )
    )
    print(f"Mensagem enviada: {routing_key} - {mensagem}")

def simular_bolsa():
    """Simula um producer enviando dados da bolsa de valores."""
    amqp_url = os.getenv('AMQP_URL')  # credenciais via ambiente
    connection, channel = conectar_rabbitmq(amqp_url)
    acoes = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3']
    try:
        for i in range(20):
            acao = random.choice(acoes)
            valor = round(random.uniform(10, 100), 2)
            variacao = round(random.uniform(-5, 5), 2)
            mensagem_cotacao = {
                'acao': acao,
                'valor': valor,
                'variacao': variacao,
                'timestamp': time.time()
            }
            routing_key = f'bolsa.cotacoes.acoes.{acao.lower()}'
            publicar_mensagem(channel, routing_key, mensagem_cotacao)
            if random.random() > 0.7:
                quantidade = random.randint(100, 10000)
                tipo = random.choice(['compra', 'venda'])
                mensagem_negociacao = {
                    'acao': acao,
                    'quantidade': quantidade,
                    'valor_total': quantidade * valor,
                    'tipo': tipo,
                    'timestamp': time.time()
                }
                routing_key = f'bolsa.negociacoes.{tipo}.{acao.lower()}'
                publicar_mensagem(channel, routing_key, mensagem_negociacao)
            time.sleep(1)
    finally:
        connection.close()
        print("Conexão fechada")

if __name__ == "__main__":
    # Defina AMQP_URL no ambiente:
    # export AMQP_URL="amqps://USUARIO:SENHA@HOST/VHOST"
    simular_bolsa()
