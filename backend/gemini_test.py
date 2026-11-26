import os, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")
model = os.getenv("GEMINI_MODEL", "")

print("key found:", bool(key), "| starts with AIza:", key.startswith("AIza"), "| length:", len(key))
print("model:", repr(model))

client = genai.Client(api_key=key)
start = time.time()
try:
    r = client.models.generate_content(model=model, contents="Say hi in one word")
    print("reply:", repr(r.text), "| took", round(time.time() - start, 1), "seconds")
except Exception as e:
    print("ERROR after", round(time.time() - start, 1), "seconds")
    print(type(e).__name__, "-", str(e)[:300])