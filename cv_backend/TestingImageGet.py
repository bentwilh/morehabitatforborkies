import requests
import json
# Define the URL to which the request will be sent
url = 'http://127.0.0.1:5000/get-image'

# Define the JSON payload to be sent in the POST request
# Note that 'body' here does not encapsulate the JSON in another layer unless explicitly required by your server.
payload = {
    "lat": -7.1499167,
    "lon": -54.7807500,
    "start_year": 2020,
    "start_month": 1,
    "end_year": 2020,
    "end_month": 12
}

# Send the POST request
response = requests.post(url, json=payload)  # Using json=payload to automatically set Content-Type to application/json

# Check if the request was successful
if response.status_code == 200:
    print('Success!')
    with open('sample.json', 'w') as output:
        output.write(response.text)  # You can process the response further if needed
else:
    print('Failed to post data.')
    print('Status code:', response.status_code)
    print('Response:', response.text)
