import asyncio
import csv

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration

CLIENT_ID = '1'

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
    writer.write(CLIENT_ID.encode())
    await asyncio.sleep(1)
    with open('../data/priority_example.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            message = ''.join(row)
            print("Sending: " + message)
            writer.write(message.encode())
            await asyncio.sleep(1)

async def receive(reader):
    while True:
        input_message = await reader.read(1024)
        f = open("../logs/client_received.txt", "a")
        f.write(input_message.decode() + '\n')
        f.close()

async def main():
    await aioquic_client()


asyncio.get_event_loop().run_until_complete(main())