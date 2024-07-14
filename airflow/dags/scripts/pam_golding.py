import requests
from bs4 import BeautifulSoup
import time
import json
import os

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


def get_property_url(urls: dict):
    base_url = "https://www.pamgolding.co.za/"
    
    # Scrape all the for-sale properties urls within the page and add them to their respective provinces
    for province, province_url in urls.items():
        print(f"Scraping {province} urls...")
        page_number = 1
        
        print(f"Scraping page {page_number}")
        while True:
            try:
                page_url = f"{province_url}/page{page_number}"
                page_response = session.get(page_url, timeout=20)
                soup = BeautifulSoup(page_response.text, "html.parser")
                
                # Checks if the the current page has content
                if not soup.find_all("div", {"class": "page-heading no-results-container notification sorry"}):
                    page_content = soup.find_all('div', {'class': 'pgp-property-image'})

                    for div in page_content[:-1]:
                        url = div.find('a', href=True)
                        property_url = (base_url + url['href'])

                        # Write the property url to the respective province file
                        mode = "w" if div == 0 else "a"
                        out_put_path = f"/opt/airflow/data/in-process-files/pam_golding/{province}.txt"

                        with open(out_put_path, mode=mode) as file:
                            file.write(property_url + "\n")
                        
                    page_number += 1
                else:
                    break
            except Exception as e:
                print(f"Error on province {province}: {e}")
                page_number += 1
                continue
    print(f"Scraping Pam Golding properties property urls...")               

def get_content():
    # Get property content from each url
    number_of_properties = 0
    province_file_path = "/opt/airflow/data/in-process-files/pam_golding"
    
    for file in os.listdir(province_file_path):
        # Remove file name extension to get province name
        province, file_extension = os.path.splitext(file)
        print(f"Scraping {province} contents...") 
        
        with open(f"{province_file_path}/{file}", 'r') as f:
            property_lst = f.read().splitlines()         
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
                        print(f"Element doesn't exist. url:{property_url}")
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

                                
                    # Upload data to S3 bucket
                    print(f"Uploading property ref:{web_ref} to S3...")
                    bucket_name = "property-data-source-bucket"
                    out_put_path = "output/pam_golding"
                    s3_bucket_upload(property_data ,f"{out_put_path}/{web_ref}.json", bucket_name)
                   
                    number_of_properties += 1 
                    time.sleep(1)
            except Exception as e:
                    print(f"Error on province {property_url}: {e}")
                    continue              
    print(f"Scraping Pam Golding properties completed. {number_of_properties} properties scraped!")          