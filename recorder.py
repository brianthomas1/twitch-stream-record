import time
from datetime import datetime
from streamlink import Streamlink
from streamlink.exceptions import NoPluginError, PluginError


CHANNEL = "https://www.twitch.tv/nats"
CHECK_INTERVAL = 30


def now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def get_stream_url(session: Streamlink, channel: str, quality: str = "best"):
    try:
        streams = session.streams(channel)

        if not streams:
            return None

        return streams.get(quality) or streams.get("best")

    except (NoPluginError, PluginError):
        return None


def record_stream(stream, channel: str):
    metadata = stream.session.resolve_url(channel)

    author = getattr(metadata, "author", "unknown")
    stream_id = getattr(metadata, "id", int(time.time()))

    filename_time = datetime.now().strftime("%d-%m-%Y_%H-%M")
    filename = f"./{author}_{filename_time}_{stream_id}.ts"

    print(f"[{now()}] Запись в файл: {filename}")

    with stream.open() as fd, open(filename, "wb") as file:
        while True:
            data = fd.read(1024 * 16)

            if not data:
                break

            file.write(data)


def main():
    session = Streamlink()

    print("Ожидание начала трансляции...")
    print(f"Канал: {CHANNEL}")
    print()

    while True:
        stream = get_stream_url(session, CHANNEL)

        if stream:
            print(f"[{now()}] Стрим начался! Запуск записи...")

            try:
                record_stream(stream, CHANNEL)
            except Exception as error:
                print(f"[{now()}] Ошибка записи: {error}")

            print(f"[{now()}] Запись завершена. Ожидание следующего стрима...")
        else:
            print(f"[{now()}] Стрим еще не начался. Проверка через {CHECK_INTERVAL} сек.")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
