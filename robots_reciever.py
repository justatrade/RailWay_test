import json
import time
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory

import numpy as np

from shape import Square, Triangle, Circle, Parallelogram

# Словарь для сопоставления имён фигур с классами
SHAPE_CLASSES = {
    "square": Square,
    "triangle": Triangle,
    "circle": Circle,
    "parallelogram": Parallelogram
}

def receive_data(queue, shm):
    print("Receiving data")
    try:
        while True:
            print("Inside main cycle")
            time.sleep(0.5)
            if not queue.empty():
                print("Queue is not empty!!!")
                size = queue.get()
                data = bytes(shm.buf[:size]).decode("utf-8")  # Чтение данных из Shared Memory
                data = json.loads(data)  # Десериализация данных

                # Получение класса фигуры из словаря
                shape_class = SHAPE_CLASSES.get(data["shape"])
                if shape_class is None:
                    print(f"Неизвестный тип фигуры: {data['shape']}")
                    continue

                # Создание экземпляра фигуры
                shape = shape_class()
                shape.points = np.array(data["points"], dtype=np.float64)

                # Отрисовка фигуры
                shape.plot(filename=f"{data['shape']}_received.png")
                print(f"Получены данные: {data['shape']}. Точки: {len(shape.points)}")
            else:
                time.sleep(0.1)  # Ожидание новых данных
    except KeyboardInterrupt:
        print("Завершение работы")

if __name__ == "__main__":
    time.sleep(1)
    shm = SharedMemory(name="robot_memory")
    queue = Queue()

    receive_data(queue, shm)

    shm.close()