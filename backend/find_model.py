import os, time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

names = [m.name.replace("models/", "") for m in client.models.list()]
# Test Gemini models only. Gemma models may not accept the system instructions the app uses.
for name in [n for n in names if n.startswith("gemini") and "flash" in n]:
    start = time.time()
    try:
        r = client.models.generate_content(model=name, contents="Say hi in one word")
        print("WORKS ", name, "->", r.text.strip(), f"({time.time()-start:.1f}s)")
    except Exception as e:
        print("FAILS ", name, "->", getattr(e, "code", type(e).__name__))