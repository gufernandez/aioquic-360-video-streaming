import asyncio

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


async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')


asyncio.ensure_future(main())
loop = asyncio.get_event_loop()
loop.run_forever()