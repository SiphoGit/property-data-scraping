import requests
from bs4 import BeautifulSoup
import time

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

def rawson_page_url_scraper():   
    try:      
        home_page_response = session.get("https://rawson.co.za/property/for-sale", timeout=20)
        soup = BeautifulSoup(home_page_response.text, "html.parser")     
        total_pages = soup.find_all('a', {'class': 'pagination__link'})[-2].text
    except Exception as e:
        print(f"Error in page 1: {e}")
    
    num_of_pages = int(total_pages)
    batch_size = 100
    page_number = 1
    
    # Scrape page urls in batches of 'batch_size'
    for i in range(0, num_of_pages): 
        print(f"Scraping Rawson properties property urls...")   
        batch_count = 0
        page_url_lst = []
        while batch_count <= batch_size:
            try:
                rawson_for_sale_url = f"https://rawson.co.za/property/for-sale?page={page_number}"
                page_response = session.get(rawson_for_sale_url, timeout=20)
                local_soup = BeautifulSoup(page_response.text, "html.parser") 
                [page_url_lst.append(link["href"]) for link in local_soup.find_all('a', {'class': 'card__link'})]
                page_number += 1
                batch_count += 1
                
                time.sleep(1)
            except Exception as e:
                print(f"Error in page {rawson_for_sale_url}: {e}")
                page_number += 1
                batch_count += 1
                continue
        
        # Write data to "rawson_page_urls.txt"
        in_process_files_path = "/opt/airflow/data/in-process-files/rawson_in_process_file.txt"
        mode = "w" if i == 0 else "a"
        
        with open(in_process_files_path, mode=mode) as file:      
            file.write('\n'.join(page_url_lst))
            
        # Reset list and batch count variable
        page_url_lst = []    
        batch_count = 0        
    print(f"Urls added to /in-process-files")

# Break file into smaller chunks
def file_chunker(file_path, chunk_size=1000):
    with open(file_path, "r") as file:
        data = file.read().splitlines()
        chunk = []
        for row in data:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

# Scrape page contents
def rawson_scraper():   
    print(f"Scraping Rawson properties page contents...") 
    in_process_files = "/opt/airflow/data/in-process-files/rawson_in_process_file.txt"
    number_of_properties = 1
    
    for chunk in file_chunker(in_process_files):
        for property_url in chunk:
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
                
                # Upload data to S3 bucket
                print(f"Uploading property ref:{web_ref} to S3...")
                bucket_name = "property-data-source-bucket"
                out_put_path = "output/rawson"
                s3_bucket_upload(property_data ,f"{out_put_path}/{web_ref}.json", bucket_name)

                number_of_properties += 1
                time.sleep(1)
            except Exception as e:
                print(f"Error in property {property_url}: {e}")
                continue         
    print(f"Scraping Rawson properties completed. {number_of_properties-1} properties scraped!")   