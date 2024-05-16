import json
import pytest
import requests

base_url = 'http://localhost:5000'

def test_add_job():
    job_data = {'bin_size': 1.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert 'id' in data
    assert data['status'] == 'submitted'

def test_get_job_by_id():
    job_data = {'bin_size': 2.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    job_id = response.json()['id']

    response = requests.get(f'{base_url}/jobs/{job_id}')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data['id'] == job_id
