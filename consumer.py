import pika
import json
import time

def conectar_rabbitmq(amqp_url, queue_name, binding_key):
    """Estabelece conexão com o RabbitMQ e configura a fila."""
    params = pika.URLParameters(amqp_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(
        exchange='bolsa',
        exchange_type='topic',
        durable=True
    )
    channel.queue_declare(
        queue=queue_name,
        durable=True
    )
    channel.queue_bind(
        exchange='bolsa',
        queue=queue_name,
        routing_key=binding_key
    )
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
    amqp_url = 'amqp://usuario:senha@servidor.cloudamqp.com/vhost'
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
    iniciar_consumer('cotacoes')
    # iniciar_consumer('negociacoes')
