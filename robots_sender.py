import time
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
from robots import Glasha, Sasha, Masha, Natasha

class QueueManager(BaseManager):
    pass

QueueManager.register('get_queue')

def run_robots():
    manager = QueueManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
    manager.connect()
    queue = manager.get_queue()

    glasha = Glasha()
    sasha = Sasha()
    masha = Masha()
    natasha = Natasha()

    shm = SharedMemory(name="robot_memory", create=True, size=262144)

    try:
        print("Ожидание 5 секунд перед отправкой данных...")
        time.sleep(5)

        for robot in [glasha, sasha, masha, natasha]:
            robot.generate_distorted_shape()
            robot.send_data(queue, shm)
            time.sleep(1)
    finally:
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    run_robots()