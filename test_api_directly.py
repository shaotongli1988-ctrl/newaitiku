#!/usr/bin/env python3
import sys
import urllib.request
import urllib.parse
import json

def test_api():
    base_url = "http://127.0.0.1:8000/api/question-bank/exam-tasks"
    params = {
        "page": 1,
        "size": 100,
        "status": "PUBLISHED",
        "taskType": "CHAPTER"
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    
    print("Testing API endpoint:", url)
    
    try:
        req = urllib.request.Request(url, headers={
            "X-Role": "teacher",
            "X-User-Id": "teacher-001"
        })
        with urllib.request.urlopen(req) as response:
            print("\n=== HTTP Status ===")
            print(f"Status code: {response.status}")
            
            print("\n=== Response Body ===")
            data = response.read()
            print(data.decode("utf-8"))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
