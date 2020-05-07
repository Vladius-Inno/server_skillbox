# К работающему серверу добавить следующий функционал:
#
# 1. При попытке подключения клиента под логином, который уже есть в чате:
#     - Отправлять клиенту текст с ошибкой "Логин {login} занят, попробуйте другой"
#     - Отключать от сервера соединение клиента
#     - Исправления будут в методе data_received у сервера
#
# 2. При успешном подключении клиента в чат:
#     - Отправлять ему последние 10 сообщений из чата
#     - Создать отдельный метод send_history и вызывать при успешой авторизации в data_received у сервера
#
# 3. Сдача домашних работ производится через Github.
#     - Создать аккаунт (если еще нет)
#     - Загрузить работу в репозиторий
#     - Проверить, что у него открытый доступ (можете открыть в режиме инкогнито)
#     - Прикрепить ссылку на репозиторий в форму SkillBox для сдачи работы (Google Формы)
#
# Форма для сдачи ДЗ - https://clck.ru/NLeZy - ТОЛЬКО В ЭТУ ФОРМУ!


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
                # Выбрал вариант с добавлением аттрибута logins в класс Server
                # Если выполнять дословно, как в ДЗ, то тогда можно было бы сделать
                # итерирование for client in self.server.clients
                # и проверить наличие client.login, совпадающего с подключающимся
                if self.login in self.server.logins:
                    print('Attempt of logging on the logged in user')
                    self.transport.write(f'Логин {self.login} занят, попробуйте другой'.encode())
                    # отрубаем клиента
                    self.transport.close()
                else:
                    self.server.logins.append(self.login)
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
    logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.logins = []
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
