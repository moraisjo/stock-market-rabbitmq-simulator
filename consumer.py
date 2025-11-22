import os
import pika
import json
import time
from urllib.parse import urlparse

def conectar_rabbitmq(amqp_url, queue_name, binding_key):
    """Conecta e garante exchange + fila (idempotente)."""
    if not amqp_url:
        raise RuntimeError("AMQP_URL não definido. Exporte: export AMQP_URL='amqps://usuario:senha@host/vhost'")

    parsed = urlparse(amqp_url)
    user = parsed.username
    vhost = parsed.path.lstrip('/') or '/'
    host = parsed.hostname
    print(f"Conectando -> host={host} vhost={vhost} user={user} ssl={'amqps' in amqp_url}")

    params = pika.URLParameters(amqp_url)
    try:
        connection = pika.BlockingConnection(params)
    except pika.exceptions.ProbableAuthenticationError as e:
        raise RuntimeError("Falha de autenticação (403). Verifique: 1) Usuário == vhost (CloudAMQP normalmente) 2) Senha correta (rotacione se necessário) 3) Vhost existe 4) Esquema amqps corresponde ao painel. URL atual: " + amqp_url) from e
    channel = connection.channel()

    def ensure_exchange(ch):
        try:
            ch.exchange_declare(exchange='bolsa', passive=True)
            return ch
        except pika.exceptions.ChannelClosedByBroker as e:
            if connection.is_open:
                ch = connection.channel()
            if 'NOT_FOUND' in str(e):
                ch.exchange_declare(exchange='bolsa', exchange_type='topic', durable=True, auto_delete=False)
                return ch
            if 'PRECONDITION_FAILED' in str(e):
                print("[consumer] Exchange 'bolsa' existe com outros argumentos. Tentando deletar e recriar...")
                try:
                    ch.exchange_delete(exchange='bolsa')
                    ch.exchange_declare(exchange='bolsa', exchange_type='topic', durable=True, auto_delete=False)
                    print("[consumer] Exchange recriado.")
                    return ch
                except Exception as del_err:
                    raise RuntimeError("Delete manual necessário via painel para 'bolsa'. Configure: type=topic durable=true auto_delete=false. Erro interno: " + str(del_err)) from del_err
            raise

    channel = ensure_exchange(channel)

    # Garantir existência da fila antes de bind.
    channel.queue_declare(queue=queue_name, durable=True, auto_delete=False)
    channel.queue_bind(exchange='bolsa', queue=queue_name, routing_key=binding_key)
    return connection, channel

def processar_mensagem(ch, method, properties, body):
    """Callback para processar mensagens recebidas."""
    try:
        mensagem = json.loads(body)
        routing_key = method.routing_key
        print(f"\nRecebida mensagem com routing key: {routing_key}")
        print(f"Conteúdo: {mensagem}")
        print("Processando mensagem...")
        time.sleep(0.5)
        if 'cotacoes' in routing_key:
            acao = mensagem['acao']
            valor = mensagem['valor']
            variacao = mensagem['variacao']
            print(f"Cotação de {acao}: R$ {valor} (variação: {variacao}%)")
            if variacao > 2:
                print(f"ALERTA: {acao} em alta expressiva!")
            elif variacao < -2:
                print(f"ALERTA: {acao} em queda expressiva!")
        elif 'negociacoes' in routing_key:
            acao = mensagem['acao']
            quantidade = mensagem['quantidade']
            valor_total = mensagem['valor_total']
            tipo = mensagem['tipo']
            print(f"Negociação de {acao}: {tipo} de {quantidade} ações por R$ {valor_total:.2f}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("Mensagem processada com sucesso!")
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def iniciar_consumer(tipo_consumer):
    """Inicia o consumer com as configurações apropriadas."""
    amqp_url = os.getenv('AMQP_URL')  # não manter credenciais hardcoded
    if tipo_consumer == 'cotacoes':
        queue_name = 'cotacoes'
        binding_key = 'bolsa.cotacoes.#'
        print("Iniciando consumer de COTAÇÕES...")
    elif tipo_consumer == 'negociacoes':
        queue_name = 'negociacoes'
        binding_key = 'bolsa.negociacoes.#'
        print("Iniciando consumer de NEGOCIAÇÕES...")
    else:
        raise ValueError(f"Tipo de consumer inválido: {tipo_consumer}")
    connection, channel = conectar_rabbitmq(amqp_url, queue_name, binding_key)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=processar_mensagem
    )
    print(f"Consumer {tipo_consumer} aguardando mensagens...")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumer interrompido pelo usuário")
    finally:
        print("Fechando conexão...")
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    # Defina AMQP_URL no ambiente para evitar credenciais em código:
    # export AMQP_URL="amqps://USUARIO:SENHA@HOST/VHOST"
    iniciar_consumer('cotacoes')
    # iniciar_consumer('negociacoes')
