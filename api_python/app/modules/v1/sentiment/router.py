from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def sentiment_test():
    return {"message": "Sentiment module is UP"}
