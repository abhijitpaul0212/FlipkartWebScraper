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
import logging
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)


application = Flask(__name__)
app = application
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(os.getenv("MONGODB_URI"))
app.db = client['web_scrape']
flipkart_coll = app.db['flipkart_scrap_data']

class WebScrape:
    def __init__(self, query) -> None:
        self.products = []
        self.ratings = []
        self.prices = []
        self.specifications = []
        self.reviews = []
        self.session = requests.Session()
        self.query = query
        self.base_url = "https://www.flipkart.com"
        self.query_url = f"/search?q={self.query}&as=on&as-show=on&otracker=AS_Query_TrendingAutoSuggest_8_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_8_0_na_na_na&as-pos=8&as-type=TRENDING&suggestionId=tv&requestId=9c9fa553-b7e5-454b-a65b-bbb7a9c74a29&page=1"

    def convert_to_df(self):
        df = pd.DataFrame({'Product Name': self.products, 'Overall Rating': self.ratings, 'Price': self.prices, 'Specification': self.specifications, 'Customer Reviews': self.reviews})
        return df
    
    def store_in_db(self, dataframe=None):
        start_time = time.perf_counter()
        
        # Deleting old entries for managing DB
        flipkart_coll.delete_many({}) 
        
        if dataframe is not None:
            dataframe.reset_index(inplace=True)
            data_dict = dataframe.to_dict("records")
            flipkart_coll.insert_many(data_dict) 
            end_time = time.perf_counter()
            logging.info("Scraped records are successfully stored in Database")
            logging.info(f"Time taken in {self.store_in_db.__name__}: {end_time - start_time}")
        else:
            logging.error("Empty dataframe cannot be stored in Database")
    
    def fetch_from_db(self):
        headings = ('Product Name', 'Overall Rating', 'Price', 'Specification', 'Customer Reviews')
        results = [(result.get(headings[0]), result.get(headings[1]), result.get(headings[2]), result.get(headings[3]), result.get(headings[4])) for result in flipkart_coll.find({})]
        return headings, results
    
    def get_products(self, url: str, master_page: bool=True):
        response = self.session.get(url)
        soup = bs(response.content, "html.parser")
        if master_page:
            return  soup.find_all(name='a', attrs={'class': '_1fQZEK'}), soup
        else:
            return soup.find_all(name='div', attrs={'class': 'col _2wzgFH K0kLPL'}), soup
    
    def fetch_prod_reviews(self, prod_url: str):
        product = prod_url.find('div', attrs={'class': '_4rR01T'})
        self.products.append(product.text if product is not None else 'NA')
        
        
        price = prod_url.find('div', attrs={'class': '_30jeq3 _1_WHN1'})
        self.prices.append(price.text if price is not None else 'NA')
        
        rating = prod_url.find('div', attrs={'class': '_3LWZlK'})
        self.ratings.append(rating.text if rating is not None else 'NA')
        
        all_spec = prod_url.find('div', attrs={'class': 'fMghEO'})
        spec = all_spec.find_all('li', class_ = 'rgWa7D')
        self.specifications.append([each_spec.text for each_spec in spec if each_spec is not None])
        
        prod_link = prod_url['href']
        final_link = self.base_url + prod_link
        final_link = final_link.replace("/p/", "/product-reviews/")
        all_rows, _ = self.get_products(url=final_link, master_page=False)
        
        review_data= []
        if all_rows != []:
            for row in all_rows:
                prod_rating = row.find('div', attrs={'class': '_3LWZlK _1BLPMq'})
                prod_rating = prod_rating.text if prod_rating is not None else 'NA'

                prod_reviewer = row.find('p', attrs={'class': '_2sc7ZR _2V5EHH'})
                prod_reviewer = prod_reviewer.text if prod_reviewer is not None else 'NA'

                prod_review_title = row.find('p', attrs={'class': '_2-N8zT'})
                prod_review_title = prod_review_title.text if prod_review_title is not None else 'NA'

                prod_review = row.find('div', attrs={'class': 't-ZTKy'})
                prod_review = prod_review.text.replace("READ MORE", "") if prod_review is not None else 'NA'
                
                review_data.append((prod_reviewer, prod_rating, prod_review_title, prod_review))
            self.reviews.append(review_data)
        else:
            self.reviews.append('NA')   

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
        
        if all([len(self.products), len(self.ratings), len(self.prices), len(self.reviews), len(self.specifications)]):
            return self.convert_to_df()
        else:
            logging.warning("Cannot parse data since one/all column(s) has zero values scraped")
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
            ws.store_in_db(dataframe=df)
            return redirect(url_for('search_results'))
        else:
            flash("No data found... try again!")
    return render_template("home.html", text="None")

@app.route("/search_results")
def search_results():
    headings = ('Product Name', 'Overall Rating', 'Price', 'Specification', 'Customer Reviews')
    results = [(result.get(headings[0]), result.get(headings[1]), result.get(headings[2]), result.get(headings[3]), result.get(headings[4])) for result in flipkart_coll.find({})]
    if results == []:
        flash("No data found in database... something is fishy!")
        logging.error("No data found in database... something is fishy!")
        return redirect(url_for('home'))
    return render_template("results.html", headings=headings, results=results)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
