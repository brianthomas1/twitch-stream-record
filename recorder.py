import os
import time
import threading
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from dotenv import load_dotenv
from streamlink import Streamlink
from streamlink.exceptions import NoPluginError, PluginError


load_dotenv()

CHANNEL = os.getenv("CHANNEL")
QUALITY = os.getenv("QUALITY", "best")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
RECORDS_DIR = os.getenv("RECORDS_DIR", "./records")

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", "8080"))

if not CHANNEL:
    raise ValueError("Переменная CHANNEL не задана в .env")

os.makedirs(RECORDS_DIR, exist_ok=True)


def now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def get_channel_name(channel_url: str) -> str:
    return channel_url.rstrip("/").split("/")[-1]


def get_stream(session: Streamlink, channel: str):
    try:
        streams = session.streams(channel)

        if not streams:
            return None

        if QUALITY in streams:
            return streams[QUALITY]

        print(
            f"[{now()}] Качество '{QUALITY}' недоступно. "
            f"Доступно: {', '.join(streams.keys())}"
        )

        return streams.get("best")

    except (NoPluginError, PluginError):
        return None
    except Exception as e:
        print(f"[{now()}] Ошибка проверки стрима: {e}")
        return None


def record_stream(stream, channel: str):
    channel_name = get_channel_name(channel)

    filename_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = os.path.join(
        RECORDS_DIR,
        f"{channel_name}_{filename_time}.ts"
    )

    print(f"[{now()}] Запись в файл: {filename}")

    with stream.open() as fd, open(filename, "wb") as file:
        while True:
            data = fd.read(1024 * 1024)

            if not data:
                break

            file.write(data)

    return filename


def start_file_server():
    handler = partial(
        SimpleHTTPRequestHandler,
        directory=RECORDS_DIR
    )

    server = ThreadingHTTPServer(
        (SERVER_HOST, SERVER_PORT),
        handler
    )

    print(
        f"[{now()}] HTTP-сервер запущен: "
        f"http://{SERVER_HOST}:{SERVER_PORT}"
    )
    print(f"[{now()}] Раздаваемая папка: {RECORDS_DIR}")

    server.serve_forever()


def main():
    server_thread = threading.Thread(
        target=start_file_server,
        daemon=True
    )
    server_thread.start()

    session = Streamlink()

    print("Ожидание начала трансляции...")
    print(f"Канал: {CHANNEL}\nКачество: {QUALITY}")
    print(f"Каталог записей: {RECORDS_DIR}\n")

    while True:
        stream = get_stream(session, CHANNEL)

        if stream:
            print(f"[{now()}] Стрим начался! Запуск записи...")

            try:
                filename = record_stream(stream, CHANNEL)
                print(f"[{now()}] Запись завершена: {filename}")
            except Exception as e:
                print(f"[{now()}] Ошибка записи: {e}")

            print(f"[{now()}] Ожидание следующего стрима...")
        else:
            print(
                f"[{now()}] Стрим еще не начался. "
                f"Проверка через {CHECK_INTERVAL} сек."
            )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
