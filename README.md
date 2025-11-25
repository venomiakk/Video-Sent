# Video-Sent

Technology Review Sentiment Analyzer

## Important

Due to frequent YT API updates, YT links may not work!

## API Keys

- Deepgram API key (required for v2 transcription module)
  - Create account at [Deepgram](https://deepgram.com/) and get your API key
  - Create file `deepgram_secret.py` in `api_python/app/core/` with content:
    ```python
    DEEPGRAM_SECRET = "your_deepgram_api_key_here"
    ```
- Groq API key (required for v2 sentiment analysis module)
  - Create account at [Groq](https://www.groq.com/) and get your API key
  - Create file `groq_secret.py` in `api_python/app/core/` with content:
    ```python
    GROQ_SECRET = "your_groq_api_key_here"
    ```

## Requirements

### Tech stack

- npm
- ffmpeg
- Python (3.13.5 >=)
- MongoDB

### Used AI models

- transcription: Deepgram API nova-2
- sentiment anlysis: Groq API

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
npm run start
```

```bash
npm start
```


https://www.instagram.com/p/DP_DL7lDAUt
