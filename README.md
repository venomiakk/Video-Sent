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

- transcription: python whisper or Deepgram API nova-2
- sentiment anlysis: https://huggingface.co/bardsai/twitter-sentiment-pl-base or Groq via API

## Current MongoDB schema

### Transcriptions collection

| Name            | Data Type  | Is Required? | Description                                                                  |
| :-------------- | :--------- | :----------- | :--------------------------------------------------------------------------- |
| `_id`           | `ObjectId` | Yes          | Unique identifier for the document.                                          |
| `link_hash`     | `String`   | Yes          | Hash (e.g. SHA-256) of the `url` field. Used for quick duplicate checking.   |
| `model`         | `String`   | No           | Model used for transcription (currently: whisperpy-base, might delete later) |
| `created_at`    | `ISODate`  | Yes          | Date and time the document was added to the database.                        |
| `title`         | `String`   | No           | Title of the video fetched from the page.                                    |
| `transcription` | `String`   | Yes          | Transcribed text from the video.                                             |
| `url`           | `String`   | Yes          | Original URL link to the video (e.g. YouTube, Instagram).                    |

### SentimentAnalysis collection

| Name            | Data Type  | Is Required? | Description                                              |
| :-------------- | :--------- | :----------- | :------------------------------------------------------- |
| `_id`           | `ObjectId` | Yes          | Unique identifier for the document.                      |
| `transcript_id` | `String`   | Yes          | ID of the associated transcription document.             |
| `model`         | `String`   | Yes          | Model used for sentiment analysis.                       |
| `created_at`    | `ISODate`  | Yes          | Date and time the document was added to the database.    |
| `results`       | `Object`   | Yes          | Sentiment analysis results, including labels and scores. |

### `Results` object structure

| Name      | Data Type | Is Required? | Description                                                          |
| :-------- | :-------- | :----------- | :------------------------------------------------------------------- |
| `Feature` | `Object`  | Yes          | Object containing sentiment analysis results for a specific feature. |

| Name         | Data Type | Is Required? | Description                                          |
| :----------- | :-------- | :----------- | :--------------------------------------------------- |
| `sentiments` | `Array`   | Yes          | Array of sentiment analysis results for the feature. |

| Name        | Data Type | Is Required? | Description                                                                         |
| :---------- | :-------- | :----------- | :---------------------------------------------------------------------------------- |
| `sentiment` | `String`  | Yes          | Sentiment label (e.g., positive, negative, neutral).                                |
| `score`     | `Float`   | No           | Confidence score for the sentiment label. (Not available with Groq API)             |
| `sentence`  | `String`  | Yes          | The sentence from the transcript that corresponds to the sentiment analysis result. |

#### Example:

```bash
"results": {
      "bateria": {
        "sentiments": [
          {
            "sentiment": "pozytywny",
            "score": 0.9996,
            "sentence": "Bateria telefonu bez problemu wytrzyma cały dzień nawet bardzo intensywnego użytkowania."
          }
        ]
      },
      "design": {
        "sentiments": [
          {
            "sentiment": "neutralny",
            "score": 0.9997,
            "sentence": "Jeżeli włożymy na niego case, to zaczyna jakoś wyglądać."
          },
        ]
      },
      "aparat": {
        "sentiments": [
          {
            "sentiment": "pozytywny",
            "score": 0.9997,
            "sentence": "Aparaty tylne są trzy i wszystkie robią świetne jakości zdjęcia."
          },
          {
            "sentiment": "pozytywny",
            "score": 0.9989,
            "sentence": "Wszystkie aparaty nagrywają w 4K, w 60 klatkach na sekundę, w HDR."
          },
        ]
      }
    }
  }
```

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

## Example transcription / video

```text
Cześć, witajcie w mojej recenzji. Na początek design - jest absolutnie premium,
świetnie leży w dłoni. Ekran to po prostu bajka, te kolory i odświeżanie 120Hz
robią wrażenie. Niestety, muszę ponarzekać na baterię. Bateria ledwo
wytrzymuje do wieczora. Serio, czas pracy jest słaby.
Aparat jest po prostu ok, robi dobre zdjęcia w dzień. W nocy jest gorzej.
Za te pieniądze spodziewałem się czegoś więcej.
```

https://www.instagram.com/p/DP_DL7lDAUt
