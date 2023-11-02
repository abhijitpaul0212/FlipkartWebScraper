## Flipkart Web Scraping

This is a mini assignment project created as a part of learning Web Scraping where the requirement is to extract information
from Flipkart Website such `Product Name`, `Price`, `Overall Rating`, foloower by detailed `customer reviews` and `ratings` using
*  BeautifulSoup
*  Requests API
*  Flask (Server)

along with 
* HTML (Frontend)
* CSS (Frontend)
* MongoDB (Data Storage) | Applied NoSQL Aggregation Pipelines

### Optimization
Using `concurrent.futures` module `multithreading` is implemented, increasing search rate of web contents along with minimising the time consumption for IO-bound tasks such logs and databases leading to a better performance of the #WebScraper application.

### Visible differences wrt to Page Loading
Previously, without optimization web scraping a single page took close to 20+ sec
With Multi-Threaded, it takes around 2.5+ secs only (Further optimization can be achieved)

### Screenshots

1. Homepage
<img width="1440" alt="image" src="https://github.com/abhijitpaul0212/FlipkartWebScraper/assets/9966441/1a772b27-8173-40ac-9eb5-ddd41b559028">

2. Result Search Page
<img width="1410" alt="image" src="https://github.com/abhijitpaul0212/FlipkartWebScraper/assets/9966441/48beb82f-f0e4-4b41-bb31-699014450c1c">


### Resources

* Deployed Project URL:- https://lnkd.in/dtsgWPQN
* GitHub Link:- https://github.com/abhijitpaul0212/FlipkartWebScraper

### Area of improvements
1. Optimise the search response rate.
2. Design the framework to be a modular one (using Blueprints)
3. Expand the host to scrap from with user provided data. (e.g. Amazon, Flipkart, Myntra, etc)
4. Will keep adding up ...
