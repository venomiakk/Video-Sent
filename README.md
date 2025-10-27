# Video-Sent

Technology Review Sentiment Analyzer

## Important

Due to frequent YT API updates, YT links may not work!

## Requirements

### Tech stack

- npm
- ffmpeg
- Python (3.13.5 >=)
- MongoDB

### Used AI models

currently used model for transcription: python whisper (base model)

consider using Deepgram API

currently used model for sentiment anlysis: https://huggingface.co/bardsai/twitter-sentiment-pl-base

consider using LLM like Groq via API

## Current MongoDB schema

### Transcriptions collection

| Name            | Data type  | Is required? | Description                                                                  |
| :-------------- | :--------- | :----------- | :--------------------------------------------------------------------------- |
| `_id`           | `ObjectId` | Yes          | Unique identifier for the document.                                          |
| `link_hash`     | `String`   | Yes          | Hash (e.g. SHA-256) of the `url` field. Used for quick duplicate checking.   |
| `model`         | `String`   | No           | Model used for transcription (currently: whisperpy-base, might delete later) |
| `created_at`    | `ISODate`  | Yes          | Date and time the document was added to the database.                        |
| `title`         | `String`   | No           | Title of the video fetched from the page.                                    |
| `transcription` | `String`   | Yes          | Transcribed text from the video.                                             |
| `url`           | `String`   | Yes          | Original URL link to the video (e.g. YouTube, Instagram).                    |

### SentimentAnalysis collection

| Name            | Data type  | Is required? | Description                                              |
| :-------------- | :--------- | :----------- | :------------------------------------------------------- |
| `_id`           | `ObjectId` | Yes          | Unique identifier for the document.                      |
| `transcript_id` | `String`   | Yes          | ID of the associated transcription document.             |
| `created_at`    | `ISODate`  | Yes          | Date and time the document was added to the database.    |
| `results`       | `Object`   | Yes          | Sentiment analysis results, including labels and scores. |

### `Results` object structure

| Name      | Data type | Description                                                          |
| :-------- | :-------- | :------------------------------------------------------------------- |
| `Feature` | `Object`  | Object containing sentiment analysis results for a specific feature. |

| Name         | Data type | Description                                          |
| :----------- | :-------- | :--------------------------------------------------- |
| `sentiments` | `Array`   | Array of sentiment analysis results for the feature. |

| Name        | Data type | Description                                                                         |
| :---------- | :-------- | :---------------------------------------------------------------------------------- |
| `sentiment` | `String`  | Sentiment label (e.g., positive, negative, neutral).                                |
| `score`     | `Float`   | Confidence score for the sentiment label.                                           |
| `sentence`  | `String`  | The sentence from the transcript that corresponds to the sentiment analysis result. |

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
npm run dev
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
