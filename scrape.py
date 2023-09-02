import json
from typing import Optional
import requests
from bs4 import BeautifulSoup

# URL of the webpage you want to scrape
URL = 'http://127.0.0.1:5000/'

def scrape(url: str) -> Optional[str]:
    # Send an HTTP GET request to the URL
    response = requests.get(url or URL)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the <meta> tag with id="bootstrap-data"
        # meta_tag = soup.find('meta', id='bootstrap-data')
        meta_tag = soup.find("body")

        # Extract the content attribute of the <meta> tag
        bootstrap_data = meta_tag['sp-bootstrap-data']

        # Parse the content as JSON
        bootstrap_data_json = json.loads(bootstrap_data)

        # Access the "tpaState" value
        tpa_state_value = bootstrap_data_json.get('tpaState')

        # Print the "tpaState" value
        return tpa_state_value

    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    return None