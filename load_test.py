import argparse
import time
import json
import threading
import urllib.request
import urllib.error
import sys
import statistics
import datetime
import random

# Global tracking for charts
request_data = []

def make_request(url, model, prompt, user_id, results, errors):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    start_time = time.time()
    status = "success"
    error_msg = ""
    
    try:
        # 5 minute timeout per request
        with urllib.request.urlopen(req, timeout=300) as response: 
            if response.status == 200:
                response.read()
            else:
                 status = "error"
                 error_msg = f"HTTP {response.status}"
                 errors.append(error_msg)
    except Exception as e:
        status = "error"
        error_msg = str(e)
        errors.append(error_msg)
    
    duration = time.time() - start_time
    
    if status == "success":
        results.append(duration)
    
    # Log data for the graph
    request_data.append({
        "timestamp": start_time,
        "duration": duration,
        "status": status,
        "user_id": user_id,
        "error": error_msg
    })

def stress_user(url, model, user_id, duration, results, errors, stop_event):
    end_time = time.time() + duration
    while time.time() < end_time and not stop_event.is_set():
        make_request(url, model, f"User {user_id}: What is the capital of France?", user_id, results, errors)
        time.sleep(1) # Small sleep to be polite-ish

def run_sustained_test(num_users, duration, url, model):
    print(f"Starting Sustained Load Test")
    print(f"Target: {url}, Model: {model}")
    print(f"maintaining {num_users} concurrent users for {duration} seconds...")
    
    threads = []
    results = []
    errors = []
    stop_event = threading.Event()
    
    for i in range(num_users):
        t = threading.Thread(target=stress_user, args=(url, model, i, duration, results, errors, stop_event))
        threads.append(t)
        t.start()
        time.sleep(0.1) # stagger start
        
    # Monitoring loop
    try:
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            print(f"Elapsed: {elapsed:.0f}s / {duration}s - Requests: {len(results)} Ok, {len(errors)} Error")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping test early...")
        stop_event.set()

    for t in threads:
        t.join()
        
    print(f"\nTest Complete. Total Requests: {len(results)}")
    if results:
        print(f"Stats:")
        print(f"  Average: {statistics.mean(results):.4f}s")
        print(f"  Median:  {statistics.median(results):.4f}s")
        print(f"  Min:     {min(results):.4f}s")
        print(f"  Max:     {max(results):.4f}s")
    
    # Save simple report
    with open('sustained_test_report.json', 'w') as f:
        json.dump(request_data, f, indent=2)


def run_batch(num_users, url, model):
    print(f"  Running batch with {num_users} users...")
    threads = []
    results = []
    errors = []
    
    for i in range(num_users):
        t = threading.Thread(target=make_request, args=(url, model, f"User {i}: What is the capital of France?", i, results, errors))
        threads.append(t)
        t.start()
        time.sleep(0.01) 
    
    for t in threads:
        t.join()
        
    return results, errors

def run_ramp_test(max_users, step_size, url, model):
    print(f"Starting Scalability Test")
    print(f"Target: {url}, Model: {model}")
    print(f"Ramping up to {max_users} users in steps of {step_size}...")
    
    current_users = step_size
    report = {
        "config": {
            "max_users": max_users,
            "step_size": step_size,
            "url": url,
            "model": model,
            "timestamp": datetime.datetime.now().isoformat()
        },
        "batches": []
    }

    while current_users <= max_users:
        print(f"\n--- Batch: {current_users} Concurrent Users ---")
        results, errors = run_batch(current_users, url, model)
        
        batch_stats = {
            "num_users": current_users,
            "successful": len(results),
            "failed": len(errors),
            "stats": {}
        }
        
        if results:
            batch_stats["stats"] = {
                "avg": statistics.mean(results),
                "median": statistics.median(results),
                "min": min(results),
                "max": max(results),
                "stdev": statistics.stdev(results) if len(results) > 1 else 0
            }
            print(f"  Avg Latency: {batch_stats['stats']['avg']:.2f}s")
            print(f"  Max Latency: {batch_stats['stats']['max']:.2f}s")
        else:
             print("  No successful requests.")
        
        if errors:
            print(f"  Errors: {len(errors)}")
            
        report["batches"].append(batch_stats)
        
        time.sleep(5)
        
        if current_users == max_users:
            break
        current_users += step_size
        if current_users > max_users: 
            current_users = max_users 

    with open('load_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    with open('load_test_raw_events.json', 'w') as f:
        json.dump(request_data, f, indent=2)

    print(f"\nTest Complete. Data saved to load_test_report.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Load test Ollama endpoint')
    parser.add_argument('--max_users', type=int, default=100, help='Max concurrent users (ramp mode)')
    parser.add_argument('--step_size', type=int, default=20, help='Users to add per step (ramp mode)')
    parser.add_argument('--duration', type=int, default=0, help='Duration in seconds for sustained test (0 = ramp mode)')
    parser.add_argument('--users', type=int, default=20, help='Concurrent users for sustained test')
    parser.add_argument('--url', type=str, default='http://localhost:8000/api/generate', help='API Endpoint')
    parser.add_argument('--model', type=str, default='gemma3:4b', help='Model name')
    
    args = parser.parse_args()
    
    # Pre-flight check
    try:
        req = urllib.request.Request(args.url.replace("/generate", "/tags"))
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status != 200:
                print("Warning: Endpoint might be unhealthy or path is wrong.")
    except Exception as e:
         print(f"Warning: Could not contact endpoint before start: {e}")
         # Continue anyway, let errors show up in report
    
    if args.duration > 0:
        run_sustained_test(args.users, args.duration, args.url, args.model)
    else:
        run_ramp_test(args.max_users, args.step_size, args.url, args.model)
