# robots_sender.py
import time
from multiprocessing import Process, Queue
from multiprocessing.shared_memory import SharedMemory
from robots import Glasha, Sasha, Masha, Natasha

def run_robots():
    # Создание роботов
    glasha = Glasha()
    sasha = Sasha()
    masha = Masha()
    natasha = Natasha()

    # Создание Shared Memory и очереди
    shm = SharedMemory(name="robot_memory", create=True, size=1024)
    queue = Queue()

    try:
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