## Пример `.env` файла
```
CHANNEL=https://www.twitch.tv/name
QUALITY=best

CHECK_INTERVAL=30

RECORDS_DIR=/data

SERVER_HOST=0.0.0.0
PORT=8080
```
Примеры значений для `QUALITY`: `1080p60`, `1080p`, `720p60`, `720p`, `best`  
Если указанное качество отсутствует у стрима, скрипт автоматически покажет список доступных качеств и переключится на `best`
