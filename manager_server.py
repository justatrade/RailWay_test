# manager_server.py
from multiprocessing.managers import BaseManager
from multiprocessing import Queue

# Создаём очередь
queue = Queue()

# Создаём менеджер
class QueueManager(BaseManager):
    pass


# Регистрируем очередь
QueueManager.register('get_queue', callable=lambda: queue)

if __name__ == "__main__":
    # Запускаем сервер менеджера
    manager = QueueManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
    server = manager.get_server()
    print("Сервер менеджера запущен на 127.0.0.1:50000")
    server.serve_forever()