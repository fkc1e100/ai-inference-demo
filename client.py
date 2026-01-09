import requests
import json
import argparse
import sys
import time

# Configuration
# Since we are running outside the cluster for this demo, we assume you are port-forwarding
# kubectl port-forward svc/ai-inference 8000:8000
BASE_URL = "http://localhost:8000"

def check_health():
    try:
        print(f"Checking connection to {BASE_URL}...")
        resp = requests.get(f"{BASE_URL}/")
        if resp.status_code == 200:
            print("✅ Connected to AI Model Service!")
            return True
        else:
            print(f"❌ Service returned status: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect. Did you run 'kubectl port-forward svc/ai-inference 8000:8000'?")
        return False

def chat(prompt, model="gemma3:4b"):
    url = f"{BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    print(f"\nThinking... (Model: {model})")
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        duration = time.time() - start_time
        
        # Pretty Print Output
        print("-" * 50)
        print(data.get("response", "No response found."))
        print("-" * 50)
        print(f"(Taxed: {duration:.2f}s)")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ask the AI Model a question")
    parser.add_argument("prompt", nargs="*", help="The question to ask")
    args = parser.parse_args()
    
    if not check_health():
        sys.exit(1)

    # Interactive Mode
    if not args.prompt:
        print("\nEntering Interactive Chat Mode (Ctrl+C to exit)")
        print("-" * 30)
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                chat(user_input)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    else:
        # One-shot mode
        chat(" ".join(args.prompt))
