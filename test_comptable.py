import base64
import requests
import json

# Chemin vers une vraie facture (image)
IMAGE_PATH = "C:/Users/claud/iaagent-backend/facture_test.jpg"

with open(IMAGE_PATH, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "image_base64": f"data:image/jpeg;base64,{image_base64}"
}

response = requests.post("http://localhost:8000/api/comptable/extract", json=payload)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))