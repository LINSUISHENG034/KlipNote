#!/usr/bin/env python3
"""Quick test script for BELLE-2 and WhisperX workers"""

import requests
import time
import sys

API_URL = "http://localhost:8000"
TEST_AUDIO = "tests/fixtures/zh_short_audio.mp3"

def test_worker(model_name):
    """Test a specific worker by model name"""
    print(f"\n{'='*60}")
    print(f"Testing {model_name.upper()} worker...")
    print(f"{'='*60}")

    # 1. Upload audio file with model parameter (automatically starts transcription)
    print(f"\n1. Uploading {TEST_AUDIO} with model={model_name}...")
    with open(TEST_AUDIO, 'rb') as f:
        files = {'file': (TEST_AUDIO, f, 'audio/mpeg')}
        data = {'model': model_name}  # Specify which worker to use
        response = requests.post(f"{API_URL}/upload", files=files, data=data)

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return False

    upload_data = response.json()
    job_id = upload_data['job_id']
    print(f"✅ Uploaded successfully: job_id={job_id}")
    print(f"   Transcription automatically started with {model_name} worker")

    # 2. Poll for result
    print(f"\n2. Waiting for transcription to complete...")
    max_wait = 120  # 2 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_URL}/status/{job_id}")
        if response.status_code != 200:
            print(f"❌ Status check failed: {response.status_code}")
            return False

        status_data = response.json()
        status = status_data['status']

        print(f"   Status: {status}", end='\r')

        if status == 'completed':
            elapsed = time.time() - start_time
            print(f"\n✅ Transcription completed in {elapsed:.1f}s")

            # Get full result
            response = requests.get(f"{API_URL}/result/{job_id}")
            if response.status_code != 200:
                print(f"❌ Failed to get result: {response.status_code}")
                return False

            result = response.json()
            print(f"\n3. Transcription Result:")
            print(f"   Segments: {len(result.get('segments', []))}")
            if result.get('segments'):
                first_seg = result['segments'][0]
                print(f"   First segment: {first_seg.get('text', 'N/A')[:50]}...")
            return True

        elif status == 'failed':
            print(f"\n❌ Transcription failed")
            print(f"   Error: {status_data.get('message', 'Unknown error')}")
            return False

        time.sleep(2)

    print(f"\n❌ Timeout waiting for transcription")
    return False

def main():
    print("KlipNote Multi-Worker Test")
    print(f"API: {API_URL}")
    print(f"Test File: {TEST_AUDIO}")

    # Test API health
    try:
        response = requests.get(f"{API_URL}/")
        print(f"✅ API is responding")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        sys.exit(1)

    # Test both workers
    results = {}
    results['belle2'] = test_worker('belle2')
    results['whisperx'] = test_worker('whisperx')

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"BELLE-2 Worker:  {'✅ PASS' if results['belle2'] else '❌ FAIL'}")
    print(f"WhisperX Worker: {'✅ PASS' if results['whisperx'] else '❌ FAIL'}")

    if all(results.values()):
        print(f"\n🎉 All workers are operational!")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some workers failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
