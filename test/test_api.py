import json
import pytest
import requests

base_url = 'http://localhost:5000'

def test_load_data():
    response = requests.post(f'{base_url}/data')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Data loaded into Redis'

def test_get_data():
    response = requests.get(f'{base_url}/data')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_delete_data():
    response = requests.delete(f'{base_url}/data')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'success'
    assert data['message'] == 'Data deleted from Redis'
    
    # Load the data back for other tests
    requests.post(f'{base_url}/data')

def test_get_exoplanets():
    response = requests.get(f'{base_url}/exoplanets')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_exoplanets_all_parameters():
    # Test with all query parameters
    query_params = {
        'min_radius': 1.0,
        'max_radius': 2.0,
        'method': 'Transit',
        'start_year': 2000,
        'end_year': 2010
    }
    response = requests.get(f'{base_url}/exoplanets', params=query_params)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_exoplanets_missing_parameters():
    # Test with missing query parameters
    query_params = {
        'min_radius': 1.0,
        'method': 'Transit'
    }
    response = requests.get(f'{base_url}/exoplanets', params=query_params)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_exoplanets_invalid_parameters():
    # Test with invalid query parameters
    query_params = {
        'min_radius': 'invalid',
        'max_radius': 'invalid'
    }
    response = requests.get(f'{base_url}/exoplanets', params=query_params)
    assert response.status_code == 400
    data = response.json()
    assert data['status'] == 'error'
    assert 'message' in data

def test_get_specific_exoplanet_data():
    response = requests.get(f'{base_url}/exoplanets')
    pl_names = response.json()
    if pl_names:
        pl_name = pl_names[0]
        response = requests.get(f'{base_url}/exoplanets/{pl_name}')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert 'pl_name' in data
    else:
        pytest.skip("No data available for testing")

def test_get_host_stars():
    response = requests.get(f'{base_url}/hosts')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_exoplanets_by_host_star():
    response = requests.get(f'{base_url}/hosts')
    hostnames = response.json()
    if hostnames:
        hostname = hostnames[0]
        response = requests.get(f'{base_url}/hosts/{hostname}')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    else:
        pytest.skip("No data available for testing")

def test_get_facilities():
    response = requests.get(f'{base_url}/facilities')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) 

def test_get_exoplanets_by_facility():
    response = requests.get(f'{base_url}/facilities')
    facilities = response.json()
    if facilities:
        facility_name = facilities[0]
        response = requests.get(f'{base_url}/facilities/{facility_name}')
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    else:
       pytest.skip("No data available for testing")

def test_help_route():
    response = requests.get(f'{base_url}/help')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict) 

def test_submit_job():
    job_data = {'bin_size': 1.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert 'id' in data
    assert data['status'] == 'submitted'

def test_get_job_ids():
    response = requests.get(f'{base_url}/jobs')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_job():
    job_data = {'bin_size': 1.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    job_id = response.json()['id']

    response = requests.get(f'{base_url}/jobs/{job_id}')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data['id'] == job_id

def test_get_result():
    job_data = {'bin_size': 1.5}
    response = requests.post(f'{base_url}/jobs', json=job_data)
    job_id = response.json()['id']

    response = requests.get(f'{base_url}/results/{job_id}')
    assert response.status_code in [200, 202, 404]
    data = response.json()
    assert isinstance(data, dict)
    assert 'status' in data
