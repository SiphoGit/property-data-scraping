import requests
from bs4 import BeautifulSoup
import time
import logging
import json

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from upload_data_s3 import s3_bucket_upload


# Create a session with retry mechanism
session = requests.Session()
retry = Retry(
    total=5, 
    backoff_factor=1, 
    status_forcelist=[500, 502, 503, 504] 
)

adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


def get_property_url(urls: dict) -> dict:
    base_url = "https://www.pamgolding.co.za/"
    
    for_sale_urls = {
         "limpopo" :[],
        "gauteng" : [],
        "north_west": [],
        "free_state": [],
        "mpumalanga": [],
        "kzn": [],
        "western_cape": [],
        "eastern_cape": [],
        "northern_cape": []       
    }

    # Scrape all the for-sale properties urls within the page and add them to their respective provinces
    for province, province_url in urls.items():
        logging.info(f"{province} urls...")
        page_number = 1
        
        while True:
            try:
                page_url = f"{province_url}/page{page_number}"
                page_response = session.get(page_url, timeout=20)
                soup = BeautifulSoup(page_response.text, "html.parser")

                if not soup.find_all("div", {"class": "page-heading no-results-container notification sorry"}):
                    page_content = soup.find_all('div', {'class': 'pgp-property-image'})

                    for div in page_content[:-1]:
                        property_url = div.find('a', href=True)
                        for_sale_urls[province].append(base_url + property_url['href'])
                    page_number += 1
                else:
                    break
            except Exception as e:
                # Handle the error, logging and skipping the page
                logging.error(f"Error on province {province}: {e}")
                page_number += 1
                continue
    logging.info("Done scraping properties urls!\n")                
    return for_sale_urls

def get_content(data: dict) -> list[dict]:
    # Get property content from each url
    properties = []
    pages = 1
    
    for province, property_lst in data.items():
        logging.info(f"Scraping {province} contents...")
        try:
            for property_url in property_lst:
                property = session.get(property_url, timeout=20)
                soup_property = BeautifulSoup(property.text, "html.parser")
            
                # Get Web reference ID
                web_ref = soup_property.find("strong", id="webreference")
                web_ref = web_ref.text if web_ref else ""
            
                # Property Overview
                property_title = soup_property.find("span", {"id": "location-text"})
                property_title = property_title.text if property_title else ""
                
                price = soup_property.find("span", {"class": "totalVal"})
                price = price.get_text(strip=True) if price else "0"
            
                # Property Details
                property_overview_element = soup_property.find("div", class_="propertyFeatures")
                
                if property_overview_element:
                    beds_element = property_overview_element.find("div", class_="propertyFeature bedroom")
                    beds = beds_element.text.strip() if beds_element else ""
                
                    baths_element = property_overview_element.find("div", class_="propertyFeature bathroom")
                    baths = baths_element.text.strip() if baths_element else ""
        
                    garages_element = property_overview_element.find("div", class_="propertyFeature garage")
                    garages = garages_element.text.strip() if garages_element else ""
                else:
                    beds = "0"
                    baths = "0"
                    garages = "0"
                
                # Features
                property_details_element = soup_property.find_all("div", {"class": "f_col"})
                property_details = [item.get_text(strip=True).replace("\n\r", "") for item in property_details_element[:-2]] if property_details_element else []
                
                parent_div = soup_property.find('div', class_='f_column left_column')
                if parent_div:
                    property_features_element = parent_div.find('ul')
                    property_features = [feature.get_text(strip=True).replace("\n\r", "") for feature in property_features_element] if property_features_element else []
                else:
                    property_features = []
                merged_features = property_details + property_features

                # Get Outside building details
                if parent_div:
                    try:
                        additional_buildings_lst = parent_div.find_all('ul')[1]
                        additional_buildings = [item for item in additional_buildings_lst if not item.find_parent("section")]
                        outside_buildings = [building.get_text(strip=True).replace("\r\n", "") for building in additional_buildings] if additional_buildings else "0"
                    except IndexError:
                        outside_buildings = "0"
                else:
                    logging.info(f"Element doesn't exist. url:{property_url}")
                    outside_buildings = "0"
                
                # Property Description
                highlight = soup_property.find("h3", {"class": "marketingHeader"})
                highlight = highlight.text if highlight else ""
                
                description_div_property_features = soup_property.find_all("section")
                description_element = description_div_property_features[2].get_text(strip=True).replace("\n", "") if len(description_div_property_features) > 2 else ""
                description = highlight + description_element
            
                property_data = [
                    {"web_reference": web_ref},
                    {"title": property_title},
                    {"province": province},
                    {"price": price},
                    {"beds": beds},
                    {"baths": baths},
                    {"garages": garages},
                    {"features": merged_features},
                    {"description": {
                        "outside_buildings": outside_buildings,
                        "property_description": description
                    }}                       
                ]

                properties.append(property_data)    
                pages += 1
                # Wait for 1 second before making the next request  
                time.sleep(1)
        except Exception as e:
                # Handle the error, logging and skipping the page
                logging.error(f"Error on province {property_url}: {e}")
                continue
            
    logging.info(f"\nPam Golding scraping is Done! {pages} scraped!\n")         
    logging.info(f"{len(properties)} Properties scraped!\n")  
    
    # Create a JSON file
    json_data = json.dumps(properties, indent=4)
    
    with open("data/pam_golding.json", "w+") as file:
        file.write(json_data)
    
    # Upload file to S3 bucket
    file_path = "data/pam_golding.json"
    key_name = "rawson_properties"    
    bucket_name = "ss-property-data-scraping"
    
    s3_bucket_upload(file_path, bucket_name, key_name)      