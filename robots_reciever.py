# robots_receiver.py
import time
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory
import matplotlib.pyplot as plt
import numpy as np

def receive_data(queue, shm):
    plt.figure(figsize=(6, 6))
    plt.title("Полученные фигуры")
    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.xlabel("X")
    plt.ylabel("Y")

    try:
        while True:
            if not queue.empty():
                size = queue.get()
                data = bytes(shm.buf[:size])  # Чтение данных из Shared Memory
                points = np.frombuffer(data, dtype=np.float64).reshape(-1, 2)  # Десериализация данных
                plt.scatter(points[:, 0], points[:, 1], label=f"Фигура {len(plt.gca().get_legend_handles_labels()[0]) + 1}")
                plt.legend()
                plt.pause(0.1)  # Обновление графика
                print(f"Получены данные: {points.shape[0]} точек")
            else:
                time.sleep(0.1)  # Ожидание новых данных
    except KeyboardInterrupt:
        print("Завершение работы")
    finally:
        plt.show()

if __name__ == "__main__":
    shm = SharedMemory(name="robot_memory")
    queue = Queue()

    receive_data(queue, shm)

    shm.close()