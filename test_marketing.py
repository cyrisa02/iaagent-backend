import requests
import json

# Chemin vers une image de flyer ou carte de visite
IMAGE_PATH = "C:/Users/claud/iaagent-backend/flyer_test.png"

with open(IMAGE_PATH, "rb") as f:
    files = {"file": ("flyer.jpg", f, "image/jpeg")}
    data = {"document_type": "flyer"}
    
    response = requests.post(
        "http://localhost:8000/api/marketing/analyze-flyer",
        files=files,
        data=data
    )

print(json.dumps(response.json(), indent=2, ensure_ascii=False))