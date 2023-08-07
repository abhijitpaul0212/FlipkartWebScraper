# WebScrapper application
import os
import time
import requests
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
from flask import Flask, render_template, request, url_for, redirect, flash
from bs4 import BeautifulSoup as bs
from concurrent.futures import ThreadPoolExecutor
import uuid
from bson.codec_options import CodecOptions, DEFAULT_CODEC_OPTIONS
from bson.binary import Binary, UuidRepresentation
import logging
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)


application = Flask(__name__)
app = application
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(os.getenv("MONGODB_URI"))
app.db = client['web_scrape']

python_opts = CodecOptions(uuid_representation=UuidRepresentation.PYTHON_LEGACY)
product_coll = app.db.get_collection('product_data', codec_options=python_opts)
review_coll = app.db.get_collection('review_data', codec_options=python_opts)

class WebScrape:
    def __init__(self, query) -> None:
        # Product details
        self.pids = []
        self.products = []
        self.overall_ratings = []
        self.prices = []
        self.specifications = []
        
        # Review details
        self.review_pids = []
        self.customer_names = []
        self.customer_ratings = []
        self.review_titles = []
        self.reviews = []
        
        self.session = requests.Session()
        self.query = query
        self.base_url = "https://www.flipkart.com"
        self.query_url = f"/search?q={self.query}&as=on&as-show=on&otracker=AS_Query_TrendingAutoSuggest_8_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_8_0_na_na_na&as-pos=8&as-type=TRENDING&suggestionId=tv&requestId=9c9fa553-b7e5-454b-a65b-bbb7a9c74a29&page=1"

    def convert_to_df(self, frame_name="product"):
        if frame_name == "product":
            df = pd.DataFrame({'P_ID': self.pids, 'Product Name': self.products, 'Overall Rating': self.overall_ratings, 'Price': self.prices})
            return df
        else:
            df = pd.DataFrame({'P_ID':self.review_pids, 'Customer Name': self.customer_names, 'Customer Rating': self.customer_ratings, 'Review Title': self.review_titles, 'Review': self.reviews})
            return df
        
    
    def store_in_db(self, collection_name, dataframe=None):
        start_time = time.perf_counter()
        
        # Deleting old entries for managing DB
        response = collection_name.delete_many({}) 
        print(f"{response.deleted_count} documents deleted as a part of cleanup activity")
        
        if dataframe is not None:
            dataframe.reset_index(inplace=True)
            data_dict = dataframe.to_dict("records")
            collection_name.insert_many(data_dict) 
            print("Data Inserted to DB")
            end_time = time.perf_counter()
            logging.info("Records inserted successfully in Database")
            logging.info(f"Time taken in {self.store_in_db.__name__}: {end_time - start_time}")
            print(f"Time taken in {self.store_in_db.__name__}: {end_time - start_time}")
        else:
            logging.error("Empty dataframe cannot be stored in Database")
    
    def get_products(self, url: str, master_page: bool=True):
        response = self.session.get(url)
        soup = bs(response.content, "html.parser")
        if master_page:
            return  soup.find_all(name='a', attrs={'class': '_1fQZEK'}), soup
        else:
            return soup.find_all(name='div', attrs={'class': 'col _2wzgFH K0kLPL'}), soup
    
    def fetch_prod_reviews(self, prod_url: str):
        pid = uuid.uuid4()
        self.pids.append(pid)
            
        product = prod_url.find('div', attrs={'class': '_4rR01T'})
        logging.info(product.text if product is not None else 'NA')
        self.products.append(product.text if product is not None else 'NA')
        
        
        price = prod_url.find('div', attrs={'class': '_30jeq3 _1_WHN1'})
        self.prices.append(price.text if price is not None else 'NA')
        
        rating = prod_url.find('div', attrs={'class': '_3LWZlK'})
        self.overall_ratings.append(rating.text if rating is not None else 'NA')
        
        prod_link = prod_url['href']
        final_link = self.base_url + prod_link
        final_link = final_link.replace("/p/", "/product-reviews/")
        all_rows, _ = self.get_products(url=final_link, master_page=False)
        
        for row in all_rows:
            prod_reviewer = row.find('p', attrs={'class': '_2sc7ZR _2V5EHH'})
            logging.info(prod_reviewer.text if prod_reviewer is not None else 'NA')
            self.customer_names.append(prod_reviewer.text if prod_reviewer is not None else 'NA')
            
            prod_rating = row.find('div', attrs={'class': '_3LWZlK _1BLPMq'})
            self.customer_ratings.append(prod_rating.text if prod_rating is not None else 'NA')

            prod_review_title = row.find('p', attrs={'class': '_2-N8zT'})
            self.review_titles.append(prod_review_title.text if prod_review_title is not None else 'NA')

            prod_review = row.find('div', attrs={'class': 't-ZTKy'})
            self.reviews.append(prod_review.text.replace("READ MORE", "") if prod_review is not None else 'NA')
        
            self.review_pids.append(list(pid for _ in range(len(self.customer_names))))
            
    def web_scrape(self, number_of_pages: int):
        start_time = time.perf_counter()
                
        final_url = self.base_url + self.query_url
        for _ in range(number_of_pages):
            all_rows, soup = self.get_products(final_url)
            
            # Multi-Threading
            with ThreadPoolExecutor(max_workers=100) as executor:
                executor.map(self.fetch_prod_reviews, all_rows)
                            
            next_page = soup.find(name='a', attrs={'class': '_1LKTO3'})
            self.query_url = next_page['href'] if next_page is not None else "There is no Next page available"
        end_time = time.perf_counter()
        logging.info(f"Time taken in {self.web_scrape.__name__}: {end_time - start_time}")
        print(f"Time taken in {self.web_scrape.__name__}: {end_time - start_time}")
        
        if all([len(self.products), len(self.overall_ratings), len(self.prices), len(self.reviews)]):
            if all([len(self.review_pids), len(self.customer_names), len(self.customer_ratings), len(self.review_titles), len(self.reviews)]):
                return self.convert_to_df(frame_name="product"), self.convert_to_df(frame_name="review")
            else:
                logging.warning("Cannot parse data since one/all review column(s) has zero values scraped")
            return None
        else:
            logging.warning("Cannot parse data since one/all product detail column(s) has zero values scraped")
            return None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        search_text = request.form.get("search")
        logging.info(f"Search Query: {search_text}")
        num_pages = request.form.get("num_pages")
        logging.info(f"Number of pages requested: {num_pages}")

        ws = WebScrape(query=search_text)
        df = ws.web_scrape(number_of_pages=int(num_pages))
        if df is not None:
            # Storing Product details
            ws.store_in_db(product_coll, dataframe=df[0])
            
            # Storing Review details
            ws.store_in_db(review_coll, dataframe=df[1])
            
            return redirect(url_for('search_results'))
        else:
            flash("No data found... try again!")
    return render_template("home.html", text="None")

@app.route("/search_results")
def search_results():
    product_headings = ('Product Name', 'Overall Rating', 'Price')
    review_headings = ('Customer Name', 'Customer Rating', 'Review Title', 'Review')
    
    aggregate_review_result = app.db.get_collection('product_data').aggregate([{
    "$lookup": 
        {"from": 'review_data',
        "localField": 'P_ID',
        "foreignField": 'P_ID',
        "as": "Review Section"}},{
            "$unset":
                ["_id", "index", "P_ID", "Review Section._id", "Review Section.index", "Review Section.P_ID"]
        }    
    ]
    )
    results = list(aggregate_review_result)

    if results == []:
        flash("No data found in database... something is fishy!")
        logging.error("No data found in database... something is fishy!")
        return redirect(url_for('home'))
    return render_template("results.html", product_headings=product_headings, review_headings=review_headings, results=results)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
