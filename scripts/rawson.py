import requests
from bs4 import BeautifulSoup
import time
import logging
import json

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from upload_data_s3 import s3_bucket_upload


# Create a session with retry mechanism when the request fails
session = requests.Session()
retry = Retry(
    total=5, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504] 
)

adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


def rawson_page_url_scraper() -> list[str]:
    home_page_response = session.get("https://rawson.co.za/property/for-sale", timeout=20)
    soup = BeautifulSoup(home_page_response.text, "html.parser")     
    total_pages = soup.find_all('a', {'class': 'pagination__link'})[-2].text
    
    page_url_lst = []

    # Loop over each for-sale page and get each property's url
    logging.info(f"Scraping Rawson properties property urls...\n") 
    for page in range(1, int(total_pages)+1):
        try:
            rawson_for_sale_url = f"https://rawson.co.za/property/for-sale?page={page}"
            page_response = session.get(rawson_for_sale_url, timeout=20)
            local_soup = BeautifulSoup(page_response.text, "html.parser") 
            [page_url_lst.append(link["href"]) for link in local_soup.find_all('a', {'class': 'card__link'})]
            
            # Wait for 1 seconds before making the next request  
            time.sleep(1)
        except Exception as e:
            # Handle the error, logging and skipping the page
            logging.error(f"Error in page {page}: {e}")
            continue
              
    return page_url_lst

def rawson_scraper(lst: list) -> list[dict]:   
    properties = []
    pages = 1
    
    logging.info(f"Scraping Rawson page Contents...\n") 
    for property_url in lst:
        try:
            property = session.get(property_url, timeout=20)
            soup_property = BeautifulSoup(property.text, "html.parser")
            
            # Property Overview
            property_title_element = soup_property.find("h1", {"class": "hero__title"})
            property_title = property_title_element.text if property_title_element else ""
            
            price_element = soup_property.find("div", {"class": "hero__price"})
            price = price_element.text if price_element else "0"

            # Details
            property_overview_element = soup_property.find_all("ol", class_="features__list")
            property_overview = [
                (item.text.split()) for item in property_overview_element if not item.find_parent("div", {"class": "card__footer"})
            ] if property_overview_element else []
            
            if property_overview:
                overview = property_overview[0]
                if len(overview) == 3:
                    beds = "0"
                    baths = "0"
                    garages = "0"
                    web_ref = overview[-1]
                elif len(overview) == 4:
                    beds = overview[0]
                    baths = "0"
                    garages = "0"
                    web_ref = overview[-1]
                elif len(overview) == 5:
                    beds = overview[0]
                    baths = overview[1]
                    garages = "0"
                    web_ref = overview[-1]
                elif len(overview) >= 6:
                    beds = overview[0]
                    baths = overview[1]
                    garages = overview[2]
                    web_ref = overview[-1]
                else:
                    beds = "0"
                    baths = "0"
                    garages = "0"
                    web_ref = ""
            else:
                beds = "0"
                baths = "0"
                garages = "0"
                web_ref = ""
        
            # Property features
            features_element = soup_property.find_all("div", {"class": "features__label"})
            property_features = [
                feature.text for feature in features_element if not feature.find_parent("li")
            ] if features_element else []
            
            # Property Description
            listing_type_elements = soup_property.find_all("div", {"class": "badge"})
            listing_type = [
                type_.text for type_ in listing_type_elements if type_.find_parent("div", {"class": "l-wrapper"})
            ] if listing_type_elements else []
            
            highlight_element = soup_property.find("p", {"class": "content-block__synopsis content-block__synopsis--highlight"})
            highlight = highlight_element.text if highlight_element else ""
            
            description_element = soup_property.find("p", {"class": "content-block__synopsis content-block__synopsis--large"})
            description_text = description_element.get_text(strip=True) if description_element else ""
            description = highlight + description_text
            
            property_data = [
                {"web_reference": web_ref},
                {"title": property_title},
                {"province": ""},
                {"price": price},
                {"beds": beds},
                {"baths": baths},
                {"garages": garages},
                {"features": property_features},
                {"description": {
                    "listing_type": listing_type,
                    "property_description": description
                }}         
            ]
            
            properties.append(property_data)
            pages += 1
            # Wait for 1 second before making the next request  
            time.sleep(1)
        except Exception as e:
            # Handle the error, logging and skipping the page
            logging.error(f"Error in property {property_url}: {e}")
            continue
        
    logging.info(f"Rawson Done! {pages} pages.")   
    logging.info(f" {len(properties)} Properties scraped!") 
    
    # Create a JSON file
    json_data = json.dumps(properties, indent=4)
    
    with open("data/raswon.json", "w+") as file:
        file.write(json_data)
    
    # Upload file to S3 bucket
    file_path = "data/raswon.json"
    key_name = "rawson_properties"    
    bucket_name = ""
    
    s3_bucket_upload(file_path, bucket_name, key_name)