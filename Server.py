import asyncio
from asyncio import transports
from typing import Optional


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes) -> None:
        # super().data_received(data)
        decoded = data.decode()
        print(decoded)
        if self.login is None:
            # login:User
            if decoded.startswith('login:'):
                self.login = decoded.replace('login:', '').replace('\r\n', '')
                # Этот вариант без добавления аттрибута logins в класс Server
                # и проверки вхождения в него
            for client in self.server.clients[:-1]:
                if client.login == self.login:
                    print('Attempt of logging on the logged in user')
                    self.transport.write(f'Логин {self.login} занят, попробуйте другой'.encode())
                    # отрубаем клиента
                    self.transport.close()
            self.transport.write(f'Hello, {self.login}\n'.encode())
            # отправляем историю с 10 (максимум) сообщеняими
            self.send_history(10)
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f'<{self.login}> {message}'
        encoded = format_string.encode()
        self.server.history.append(format_string)
        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def send_history(self, number_messages):
        # print(self.server.history[-int(number_messages):])
        if self.server.history:
            self.transport.write(f'The last messages in the chat:\n'.encode())
            hist_messages = '\n'.join(x for x in self.server.history[-int(number_messages):])
            self.transport.write(hist_messages.encode())

    def connection_made(self, transport: transports.Transport) -> None:
        # super().connection_made(transport)
        self.transport = transport
        self.server.clients.append(self)
        print('Connection made')

    def connection_lost(self, exc: Optional[Exception]) -> None:
        # super().connection_lost(exc)
        self.server.clients.remove(self)
        print('Connection lost')


class Server:
    clients: list
    # logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(self.create_protocol, '127.0.0.1', 8888)
        print('Server started')
        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print('Server stopped manually')
