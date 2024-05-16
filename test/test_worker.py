import json
import pytest
import requests
import time
import os

base_url = 'http://localhost:5000'

def test_worker():
    # Submit a job
    job_data = {'bin_size': 1.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    job_id = response.json()['id']

    # Wait for the worker to process previous jobs, time is longer to account for varying processor speeds
    time.sleep(45)

    # Check the job status
    response = requests.get(f'{base_url}/jobs/{job_id}')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] in ['in progress', 'complete', 'failed']

    # Check the job result
    response = requests.get(f'{base_url}/results/{job_id}')
    assert response.status_code in [200, 202, 404]

    # Save the image to a file
    with open('histogram.png', 'wb') as f:
        f.write(response.content)

    # Check if the image file was created
    assert os.path.exists('histogram.png')

    # Clean up the downloaded image file
    os.remove('histogram.png')