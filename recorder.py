import os
import time
from datetime import datetime

from dotenv import load_dotenv
from streamlink import Streamlink
from streamlink.exceptions import NoPluginError, PluginError

load_dotenv()

CHANNEL = os.getenv("CHANNEL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
RECORDS_DIR = os.getenv("RECORDS_DIR", "./records")

if not CHANNEL:
    raise ValueError("Переменная CHANNEL не задана в .env")

os.makedirs(RECORDS_DIR, exist_ok=True)


def now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def get_stream(session: Streamlink, channel: str):
    try:
        streams = session.streams(channel)

        if not streams:
            return None

        return streams.get("best")

    except (NoPluginError, PluginError):
        return None
    except Exception as e:
        print(f"[{now()}] Ошибка проверки стрима: {e}")
        return None


def get_channel_name(channel_url: str) -> str:
    return channel_url.rstrip("/").split("/")[-1]


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


def main():
    session = Streamlink()

    print("Ожидание начала трансляции...")
    print(f"Канал: {CHANNEL}")
    print(f"Каталог записей: {RECORDS_DIR}")
    print()

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
