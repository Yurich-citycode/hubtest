# Готовые ролики

Здесь лежат смонтированные видео. Файлы весят десятки мегабайт, поэтому на GitHub они открываются
медленно — удобнее скачивать из релиза: [github.com/Yurich-citycode/hubtest/releases](https://github.com/Yurich-citycode/hubtest/releases).

| Файл | Длительность | Разрешение | Размер | Что в кадре |
| --- | --- | --- | --- | --- |
| `yurichhub-intro-1080p.mp4` | 12 с | 1920×1080 | 1,9 МБ | Интро: знак YURICHHUB, «Открыть. Войти. Владеть.» с карточками четырёх модулей, формула из канона, вход в канал |
| `site-tour-1080p.mp4` | 50 с | 1920×1080 | 45 МБ | Тур по сайту-хабу: главная, Sevastopol AI, City Code, Crimea RWA, курс, ЦФА, финал. Мастер для пережатия и монтажа |
| `site-tour-1080p-web.mp4` | 50 с | 1920×1080 | 11 МБ | То же для веба и мессенджеров: CRF 21, faststart, без звука |
| `batch/cfa-ne-token.mp4` | 8 с | 1080×1920 | 3,7 МБ | Вертикальный пост: ЦФА, «Не токен», цифры 80 000 / 0 / 259-ФЗ |
| `batch/rwa-snachala-aktiv.mp4` | 8 с | 1080×1920 | 3,7 МБ | Вертикальный пост: Crimea RWA, «Сначала / актив», блоки А · Б · В |
| `batch/course-bez-signalov.mp4` | 8 с | 1080×1920 | 3,7 МБ | Вертикальный пост: курс YuRich RWA, «Без / сигналов», шесть модулей |

## Как собрать заново

```bash
cd video
bash setup.sh                                     # один раз
bash bin/hf.sh render projects/yurichhub-intro -o renders/yurichhub-intro-1080p.mp4
bash bin/hf.sh render projects/site-tour -o renders/site-tour-1080p.mp4 --workers 2
bash bin/hf.sh render projects/social-post-vertical \
  --batch projects/social-post-vertical/batch.example.json -o "renders/batch/{output}"
```

Полное описание студии — [../README.md](../README.md), разбор пяти репозиториев — [../STUDY.md](../STUDY.md).
