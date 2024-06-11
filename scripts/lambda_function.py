import pam_golding
import rawson

from upload_data_s3 import s3_bucket_upload
from inputs import provinces_urls

def lambda_handler():
    #Scrape Rawson properties
    property_url_lst = rawson.rawson_page_url_scraper()
    rawson.rawson_scraper(property_url_lst)
    
    # Scrape Pam Golding properties
    pam_province_urls = pam_golding.get_property_url(provinces_urls)
    pam_golding.get_content(pam_province_urls)
      
lambda_handler()