import asyncio
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration

list_of_users = []

async def handle_echo(reader, writer):
    name = await reader.read(1024)
    name.decode()
    print(name)

    addr = writer
    list_of_users.append(addr)

    while True:
        data = await reader.read(1024)
        message = data.decode()
        print(message)
        if not message:
            list_of_users.remove(addr)
            break
        msg(message)


def msg(message):
    for user in list_of_users:
        print('send message - ', message)
        user.write(message.encode())


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