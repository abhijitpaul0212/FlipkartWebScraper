from flask import Flask, render_template, request, url_for, redirect, flash
from bs4 import BeautifulSoup as bs
import os
import requests
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(os.getenv("MONGODB_URI"))
app.db = client['web_scrape']
flipkart_coll = app.db['flipkart_scrap_data']

class WebScrape:
    def __init__(self, query) -> None:
        self.query = query
        self.products = []
        self.ratings = []
        self.prices = []
        self.specifications = []
        self.reviews = []

    def store_in_df(self):
        if all([len(self.products), len(self.ratings), len(self.prices), len(self.reviews), len(self.specifications)]):
            df = pd.DataFrame({'Product Name': self.products, 'Customer Ratings': self.ratings, 'Price': self.prices, 'Specification': self.specifications, 'Reviews': self.reviews})
            print(df.head(10))
            return df
        else:
            print("Cannot store data since one/all column(s) has zero values scrapped")
    
    def store_in_db(self):
        
        # Deleting old entries for managing DB
        flipkart_coll.delete_many({}) 
        
        df = self.store_in_df()
        print(df)
        if df is not None:
            df.reset_index(inplace=True)
            data_dict = df.to_dict("records")
            flipkart_coll.insert_many(data_dict) 


    def web_scrape(self):
        base_url = "https://www.flipkart.com"
        query_url = f"/search?q={self.query}&as=on&as-show=on&otracker=AS_Query_TrendingAutoSuggest_8_0_na_na_na&otracker1=AS_Query_TrendingAutoSuggest_8_0_na_na_na&as-pos=8&as-type=TRENDING&suggestionId=tv&requestId=9c9fa553-b7e5-454b-a65b-bbb7a9c74a29&page=1"
        final_url = base_url + query_url
        for _ in range(2):
            response = requests.get(final_url)
            if response.status_code != 200:
                break
            soup = bs(response.content, "html.parser")
            all_rows = soup.find_all(name='a', attrs={'class': '_1fQZEK'})
            
            for row in all_rows:
                product = row.find('div', attrs={'class': '_4rR01T'})
                self.products.append(product.text if product is not None else 'NA')
                
                
                price = row.find('div', attrs={'class': '_30jeq3 _1_WHN1'})
                self.prices.append(price.text if price is not None else 'NA')
                
                rating = row.find('div', attrs={'class': '_3LWZlK'})
                self.ratings.append(rating.text if rating is not None else 'NA')
                
                all_spec = row.find('div', attrs={'class': 'fMghEO'})
                spec = all_spec.find_all('li', class_ = 'rgWa7D')
                self.specifications.append([each_spec.text for each_spec in spec if each_spec is not None])
                
                prod_link = row['href']
                final_link = base_url + prod_link
                final_link = final_link.replace("/p/", "/product-reviews/")
                prod_page = requests.get(final_link)
                prod_soup = bs(prod_page.content, "html.parser")
                all_review_rows = prod_soup.find_all(name='div', attrs={'class': 'col _2wzgFH K0kLPL'})
                prod_review = []
                if all_review_rows != []:
                    for row in all_review_rows:
                        review = row.find('p', attrs={'class': '_2-N8zT'})
                        prod_review.extend([review.text if review is not None else 'NA'])
                    self.reviews.append(prod_review)
                else:
                    self.reviews.append('NA')
                
            next_page = soup.find(name='a', attrs={'class': '_1LKTO3'})
            query_url = next_page['href'] if next_page is not None else "There is no Next page available"
            

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        search_text = request.form.get("search")
        ws = WebScrape(query=search_text)
        ws.web_scrape()
        ws.store_in_db()
        return redirect(url_for('search_results'))
    return render_template("home.html", text="None")

@app.route("/search_results")
def search_results():
    headings = ('Product Name', 'Customer Ratings', 'Price', 'Specification', 'Reviews')
    results = []
    for result in flipkart_coll.find({}):
        results.append((result.get(headings[0]), result.get(headings[1]), result.get(headings[2]), result.get(headings[3]), result.get(headings[4])))
    if results == []:
        flash("No data found... try again!")
        return redirect(url_for('home'))
    return render_template("results.html", headings=headings, results=results)

if __name__ == '__main__':
    app.run(debug=True)