import os
import time
import threading
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from dotenv import load_dotenv
from streamlink import Streamlink
from streamlink.exceptions import NoPluginError, PluginError


load_dotenv()

CHANNEL = os.getenv("CHANNEL")
QUALITY = os.getenv("QUALITY", "best")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

RECORDS_DIR = os.getenv("RECORDS_DIR", "./records")

HTTP_SERVER_ENABLED = os.getenv("HTTP_SERVER_ENABLED", "true").lower() in (
    "true",
    "yes",
    "on",
)

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", "8080"))

if not CHANNEL:
    raise ValueError("Переменная CHANNEL не задана в .env")

os.makedirs(RECORDS_DIR, exist_ok=True)

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index():
    items = []

    for filename in sorted(os.listdir(RECORDS_DIR), reverse=True):
        path = os.path.join(RECORDS_DIR, filename)

        if os.path.isfile(path):
            items.append(
                f'<li><a href="/files/{filename}" target="_blank">{filename}</a></li>'
            )

    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Records</title>
    </head>
    <body>
        <h1>Records</h1>
        <ul>
            {''.join(items)}
        </ul>
    </body>
    </html>
    """


@app.get("/files/{filename}")
def get_file(filename: str):
    records_dir = os.path.abspath(RECORDS_DIR)
    path = os.path.abspath(os.path.join(records_dir, filename))

    if not path.startswith(records_dir + os.sep):
        raise HTTPException(status_code=403, detail="Forbidden")

    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "video/mp4" if filename.lower().endswith(".mp4") else "video/mp2t"

    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
    )


def start_file_server():
    print(f"[{now()}] HTTP-сервер запущен: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"[{now()}] Раздаваемая папка: {RECORDS_DIR}")

    uvicorn.run(
        app,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="warning",
    )


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
        f"{channel_name}_{filename_time}_{QUALITY}.ts"
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
        directory=RECORDS_DIR,
    )

    server = ThreadingHTTPServer(
        (SERVER_HOST, SERVER_PORT),
        handler,
    )

    print(
        f"[{now()}] HTTP-сервер запущен: "
        f"http://{SERVER_HOST}:{SERVER_PORT}"
    )
    print(f"[{now()}] Раздаваемая папка: {RECORDS_DIR}")

    server.serve_forever()


def main():
    if HTTP_SERVER_ENABLED:
        server_thread = threading.Thread(
            target=start_file_server,
            daemon=True,
        )
        server_thread.start()
    else:
        print(f"[{now()}] HTTP-сервер отключен")

    session = Streamlink()

    print("Ожидание начала трансляции...")
    print(f"Канал: {CHANNEL}")
    print(f"Качество: {QUALITY}")
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
