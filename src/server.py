import asyncio
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from priority_queue import StrictPriorityQueue

async def handle_echo(reader, writer):
    queue = StrictPriorityQueue()
    name = await reader.read(1024)
    name.decode()
    print(name)

    asyncio.ensure_future(receive(reader, queue))
    while True:
        tile = await queue.get()
        send(str(tile), writer)

async def receive(reader, queue):
    while True:
        input_message = await reader.read(1024)
        print('Appending: '+str(input_message.decode()))
        data = str(input_message.decode()).split(';')
        first = True
        for item in data:
            if first:
                first = False
            else:
                tile = eval(item[1:-1])
                queue.put_nowait(tile)

def send(message, writer):
    print('send message - ', message)
    writer.write(message.encode())

def handle_stream(reader, writer):
    asyncio.ensure_future(handle_echo(reader, writer))

async def main():
    configuration = QuicConfiguration(
        is_client=False,
        max_datagram_frame_size=65536
    )

    configuration.load_cert_chain('../cert/ssl_cert.pem', '../cert/ssl_key.pem')

    await serve('127.0.0.1',
                8888,
                configuration=configuration,
                stream_handler=handle_stream,)


asyncio.ensure_future(main())
loop = asyncio.get_event_loop()
loop.run_forever()