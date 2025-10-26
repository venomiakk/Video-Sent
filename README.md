# Video-Sent

Technology Review Sentiment Analyzer

## Requirements

- npm
- ffmpeg
- Python (3.13.5 >=)
- MongoDB

## How to run

### python api:

run app:

```bash
uvicorn app.main:app --reload
```

run unit tests:

```bash
pytest .\tests\test_downloader.py
```

run coverage check:

```bash
pytest --cov=app --cov-report=term-missing -q
```

run coverage check with html report:

```bash
pytest --cov=app --cov-report=html
```

### react ui:

```bash
npm run dev
```
