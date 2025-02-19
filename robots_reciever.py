import time
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
import json
import numpy as np
from shape import Square, Triangle, Circle, Parallelogram

SHAPE_CLASSES = {
    "square": Square,
    "triangle": Triangle,
    "circle": Circle,
    "parallelogram": Parallelogram
}

class QueueManager(BaseManager):
    pass

QueueManager.register('get_queue')

def receive_data():
    print("Receiving data")

    manager = QueueManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
    manager.connect()
    queue = manager.get_queue()

    shm = SharedMemory(name="robot_memory")

    try:
        while True:
            print("Inside main cycle")
            time.sleep(0.5)
            if not queue.empty():
                print("Queue is not empty!!!")
                size = queue.get()
                data = bytes(shm.buf[:size]).decode("utf-8")
                data = json.loads(data)

                shape_class = SHAPE_CLASSES.get(data["shape"])
                if shape_class is None:
                    print(f"Неизвестный тип фигуры: {data['shape']}")
                    continue

                shape = shape_class()
                shape.points = np.array(data["points"], dtype=np.float64)
                shape.plot(filename=f"{data['shape']}_received.png")
                print(f"Получены данные: {data['shape']}. Точки: {len(shape.points)}")
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Завершение работы")
    finally:
        shm.close()

if __name__ == "__main__":
    time.sleep(1)
    receive_data()