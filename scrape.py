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
        # soup = BeautifulSoup(response.text, 'html.parser')

        # Decode the HTML content from bytes to a string
        html_content_str = response.content.decode("utf-8")

        # Create a BeautifulSoup object to parse the HTML
        soup = BeautifulSoup(html_content_str, "html.parser")

        # Extract the text content of the HTML document
        # text_content = soup.get_text()

        # # Find the <meta> tag with id="bootstrap-data"
        meta_tag = soup.find('meta', id='bootstrap-data')
        # meta_tag = soup.find("body")

        # # Extract the content attribute of the <meta> tag
        bootstrap_data = meta_tag['sp-bootstrap-data']

        # # Parse the content as JSON
        bootstrap_data_json = json.loads(bootstrap_data)

        # # Access the "tpaState" value
        tpa_state_value = bootstrap_data_json.get('tpaState')

        # # Print the "tpaState" value
        return tpa_state_value
        # return text_content

    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    return None
