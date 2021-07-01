import asyncio
from aioconsole import ainput
from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration

async def aioquic_client():
    configuration = QuicConfiguration(is_client=True)
    configuration.load_verify_locations('../cert/pycacert.pem')
    async with connect('127.0.0.1', 8888, configuration=configuration) as client:
        connection_protocol = QuicConnectionProtocol
        reader, writer = await connection_protocol.create_stream(client)
        await handle_stream(reader, writer)

async def handle_stream(reader, writer):
    # User input
    asyncio.ensure_future(receive(reader))
    # Server data received
    while True:
        await send(writer)

async def send(writer):
    message = await ainput()
    writer.write(message.encode())


async def receive(reader):
    while True:
        input_message = await reader.read(1024)
        print('print incoming message', input_message)


async def main():
    await aioquic_client()


asyncio.get_event_loop().run_until_complete(main())