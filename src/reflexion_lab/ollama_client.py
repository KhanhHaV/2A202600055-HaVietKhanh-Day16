import urllib.request
import json
import time

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:1.5b-instruct"  

def chat_ollama(system_prompt: str, user_prompt: str, json_format: bool = False) -> tuple[str, int, int]:
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    if json_format:
        payload["format"] = "json"
        
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={'Content-Type': 'application/json'})
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120.0) as response:
            result = json.loads(response.read().decode('utf-8'))
            latency_ms = int((time.time() - start_time) * 1000)
            
            content = result["message"]["content"]
            tokens = result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
            return content, tokens, latency_ms
    except Exception as e:
        print(f"Ollama API error: {e}")
        return "{}", 0, 0
