import asyncio
from aioconsole import ainput

async def aioquic_client():
    # Connection
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

    # Initial message
    name = input('Enter your name: ')
    writer.write(name.encode())

    # User input
    asyncio.ensure_future(incoming_messages(reader))
    # Server data received
    while True:
        await output_messages(writer)


async def output_messages(writer):
    message = await ainput()
    writer.write(message.encode())


async def incoming_messages(reader):
    while True:
        input_message = await reader.read(1024)
        print('print incoming message', input_message)


async def main():
    await aioquic_client()


asyncio.get_event_loop().run_until_complete(main())