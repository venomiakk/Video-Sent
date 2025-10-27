import datetime
import nltk
from transformers import pipeline
import logging
import threading
from typing import Optional, Any
from app.modules.v1.transcription.service import db
from .schemas import ASPECT_KEYWORDS
from bson import ObjectId

MODEL_NAME = "bardsai/twitter-sentiment-pl-base"

_classifier_lock = threading.Lock()
_classifier: Optional[Any] = None


def _initialize_nltk() -> None:
    """Ensure required NLTK resources are available."""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        logging.info("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt')
        nltk.download('punkt_tab')


def get_classifier() -> Any:
    """Return a cached sentiment classifier, loading resources on first use.

    Thread-safe: uses a lock to ensure only one load occurs.
    """
    global _classifier
    if _classifier is not None:
        return _classifier

    with _classifier_lock:
        if _classifier is not None:
            return _classifier

        logging.info("✅    Initializing NLTK resources and sentiment analysis pipeline (lazy)...")
        # prepare NLTK
        try:
            _initialize_nltk()
        except Exception as e:
            logging.error(f"❌    Error initializing NLTK resources: {e}")
            raise

        logging.info("✅    Loading sentiment analysis model...")
        try:
            _classifier = pipeline("sentiment-analysis", model=MODEL_NAME)
            return _classifier
        except Exception as e:
            logging.error(f"❌    Error loading sentiment analysis model: {e}")
            raise

def _translate_sentiment_label(label: str) -> str:
    """Translate sentiment label from English to Polish."""
    if label.lower() == 'positive':
        return 'pozytywny'
    if label.lower() == 'negative':
        return 'negatywny'
    return 'neutralny'

async def save_results_to_db(transcription_id: str, transcription_model: str, analysis_results: dict) -> None:
    """Save sentiment analysis results to the database."""
    try:
        await db.sentiment_analysis.insert_one({
            "transcription_id": transcription_id,
            "model": transcription_model,
            "results": analysis_results,
            "created_at": datetime.datetime.now(tz=datetime.timezone.utc)
        })
        logging.info(f"✅    Saved sentiment analysis results to DB for transcription_id: {transcription_id}")
    except Exception as e:
        logging.error(f"❌    Error saving sentiment analysis results to DB: {e}")

async def analyze(
    transcription_id: str,
    classifier_pipeline: Optional[Any] = None,
    aspect_keywords_map: dict = ASPECT_KEYWORDS,
) -> list[dict]:
    """
    Analyze the transcription text for sentiment on predefined aspects.

    Args:
        transcription_text (str): The transcription text to analyze.
        classifier_pipeline: The sentiment analysis pipeline.
        aspect_keywords_map (dict): Mapping of aspects to their keywords.

    Returns:
        list[dict]: List of dictionaries containing aspect and its sentiment.
    """

    try:
        oid = ObjectId(transcription_id)
    except Exception:
        logging.error(f"Invalid transcription_id (not an ObjectId): {transcription_id}")
        return []  

    try:
        doc = await db.transcriptions.find_one({"_id": oid})
    except Exception as e:
        logging.error(f"❌    Error fetching transcription from DB: {e}")
        return []
    
    try:
        transcription_text = doc["transcription"] if doc else ""
        transcription_model = doc["model"] if doc else ""
    except Exception as e:
        logging.error(f"❌    Error accessing transcription text: {e}")
        return []

    existing = await db.sentiment_analysis.find_one({"transcription_id": transcription_id, "model": transcription_model})
    if existing:
        logging.info(f"✅    Found existing sentiment analysis results for transcription_id: {transcription_id}")
        return existing["results"]
    
    if not transcription_text:
        return []

    # lazy-init classifier when not provided
    if classifier_pipeline is None:
        try:
            classifier_pipeline = get_classifier()
        except Exception:
            logging.error("❌    Failed to initialize sentiment classifier")
            return []
    
    results = []
    processed_sentences = set()

    try:
        sentences = nltk.sent_tokenize(transcription_text, language='polish')
    except Exception as e:
        logging.error(f"❌    Error during sentence tokenization: {e}")
        sentences = [transcription_text]

    for sentence in sentences:
        sentence_clean = sentence.strip()

        if not sentence_clean or sentence_clean in processed_sentences:
            continue

        processed_sentences.add(sentence_clean)
        sentence_lower = sentence_clean.lower()
        found_aspects = set()

        for aspect, keywords in aspect_keywords_map.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    found_aspects.add(aspect)
                    break
        if found_aspects:
            try:
               sentiment = classifier_pipeline(sentence_clean)[0]
               sentiment_label = _translate_sentiment_label(sentiment['label'])
               score = sentiment['score']

               for aspect in found_aspects:
                   results.append({
                       "aspect": aspect,
                       "sentiment": sentiment_label,
                       "score": round(score, 4),
                       "sentence": sentence_clean
                   })
            
            except Exception as e:
                logging.error(f"❌    Error during sentiment analysis: {e}")

    formatted_results = dict()
    for res in results:
        aspect = res["aspect"]
        if aspect not in formatted_results:
            formatted_results[aspect] = {
                "sentiments": []
            }
        formatted_results[aspect]["sentiments"].append({
            "sentiment": res["sentiment"],
            "score": res["score"],
            "sentence": res["sentence"]
        })
    await save_results_to_db(transcription_id, transcription_model, formatted_results)
    return formatted_results

