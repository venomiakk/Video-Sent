import datetime
from bson import ObjectId
from app.core.sentiment_keywords import ASPECT_KEYWORDS
from app.core.groq_secret import GROQ_SECRET
import logging
from app.core.database import db
from groq import Groq, APIError
import json

async def save_results_to_db(transcription_id: str, analysis_model: str, analysis_results: dict) -> None:
    """Save sentiment analysis results to the database."""
    try:
        await db.sentiment_analysis.insert_one({
            "transcription_id": transcription_id,
            "model": analysis_model,
            "results": analysis_results,
            "created_at": datetime.datetime.now(tz=datetime.timezone.utc)
        })
        logging.info(f"✅    Saved sentiment analysis results to DB for transcription_id: {transcription_id}")
    except Exception as e:
        logging.error(f"❌    Error saving sentiment analysis results to DB: {e}")


async def analyze(transcript_id: str, analysis_model: str = "llama-3.3-70b-versatile") -> list[dict]:
    """
    Analyze sentiment for a given transcription ID.\n
    Uses Groq API with llama-3.3-70b-versatile model.
    """

    try: 
        oid = ObjectId(transcript_id)
    except Exception:
        logging.error(f"Invalid transcription_id (not an ObjectId): {transcript_id}")
        return []
    
    try:
        doc = await db.transcriptions.find_one({"_id": oid})
    except Exception as e:
        logging.error(f"❌    Error fetching transcription from DB: {e}")
        return []
    
    try:
        transcription_text = doc["transcription"] if doc else ""
    except Exception as e:
        logging.error(f"❌    Error accessing transcription text: {e}")
        return []
    
    existing = await db.sentiment_analysis.find_one({"transcription_id": transcript_id, "model": analysis_model})
    if existing:
        logging.info(f"✅    Found existing sentiment analysis results for transcription_id: {transcript_id}")
        return existing["results"]
    
    if not transcription_text:
        return []

    ASPECT_LIST = ASPECT_KEYWORDS.keys()

    client = Groq(api_key=GROQ_SECRET)

    system_prompt = f"""
    Jesteś ekspertem od analizy sentymentu polskich recenzji telefonów. 
    Twoim zadaniem jest przeanalizować tekst dostarczony przez użytkownika.
    
    Skup się WYŁĄCZNIE na znalezieniu opinii dotyczących następujących aspektów:
    {', '.join(ASPECT_LIST)}

    Zasady odpowiedzi:
    1.  Musisz odpowiedzieć WYŁĄCZNIE w formacie JSON.
    2.  Twój JSON musi mieć jeden główny klucz o nazwie "results".
    3.  Wartością klucza "results" musi być obiekt (słownik).
    4.  Kluczami w tym obiekcie "results" mogą być TYLKO nazwy aspektów, o których 
        znalazłeś wzmiankę (np. "bateria", "aparat" itd.).
    5.  NIE umieszczaj w "results" kluczy dla aspektów, o których nie ma mowy w tekście.
    6.  Każdy klucz aspektu (np. "bateria") musi zawierać obiekt z jednym kluczem: "sentiments".
    7.  "sentiments" musi być listą (Array) obiektów.
    8.  Każdy obiekt w liście "sentiments" musi mieć DOKŁADNIE dwa klucze:
        - "sentiment": (jeden z: "pozytywny", "negatywny", "neutralny")
        - "sentence": (dokładny cytat z tekstu, który potwierdza opinię)
    
    Przykład struktury dla jednego aspektu:
    {{
      "results": {{
        "bateria": {{
          "sentiments": [
            {{
              "sentiment": "pozytywny",
              "sentence": "Bateria jest świetna."
            }}
          ]
        }}
      }}
    }}
    
    Pamiętaj: jeśli tekst wspomina o "baterii" 3 razy, klucz "bateria" powinien
    mieć 3 obiekty w swojej liście "sentiments".
    Jeśli nie znajdziesz niczego, zwróć: {{"results": {{}} }}
    """

    logging.info(f"🔍  Analyzing sentiment for transcription_id: {transcript_id} using model: {analysis_model}")

    try:
        chat_completion = client.chat.completions.create(
            model=analysis_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcription_text}
            ],
            response_format={"type": "json_object"},
            temperature=0.1 
        )

        response_content = chat_completion.choices[0].message.content
        analysis_results = json.loads(response_content)
        analysis_results = analysis_results.get("results", {})
        await save_results_to_db(transcript_id, analysis_model, analysis_results)
        return analysis_results

    except APIError as e:
        print(f"API Groq Error: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Error: API Groq did not return a valid JSON format.")
        print(f"Received: {response_content}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
