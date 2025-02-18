# robots_sender.py
import time
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
from robots import Glasha, Sasha, Masha, Natasha

# Создаём менеджер
class QueueManager(BaseManager):
    pass

# Регистрируем очередь
QueueManager.register('get_queue')

def run_robots():
    # Подключаемся к серверу менеджера
    manager = QueueManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
    manager.connect()
    queue = manager.get_queue()

    # Создание роботов
    glasha = Glasha()
    sasha = Sasha()
    masha = Masha()
    natasha = Natasha()

    # Создание Shared Memory
    shm = SharedMemory(name="robot_memory", create=True, size=16536)  # Увеличенный размер памяти

    try:
        # Задержка перед запуском
        print("Ожидание 5 секунд перед отправкой данных...")
        time.sleep(5)

        # Генерация и отправка данных
        for robot in [glasha, sasha, masha, natasha]:
            robot.generate_distorted_shape()
            robot.send_data(queue, shm)
            time.sleep(1)  # Пауза между отправками
    finally:
        # Освобождение ресурсов
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    run_robots()