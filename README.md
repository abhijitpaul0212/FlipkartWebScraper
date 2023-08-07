## Flipkart Web Scrapping

This is a mini assignment project created a part of learning WebScrapping using
*  BeautifulSoup
*  Requests API
*  Flask (Server)

along with 
* HTML (Frontend)
* CSS (Frontend)
* MongoDB (Data Storage) | Applied Aggregation Pipeline

### Optimization
Using `concurrent.futures` module `multithreading` is implemented, increasing search rate of web contents along with minimising the time consumption for IO-bound tasks such logs and databases leading to a better performance of the #WebScraper application.

Deployed Project URL:- https://lnkd.in/dtsgWPQN
GitHub Link:- https://github.com/abhijitpaul0212/FlipkartWebScraper

### Visible differences wrt to Page Loading
Previously, without optimization web scraping a single page took close to 20+ sec
With Multi-Threaded, it takes around 2.5+ secs only (Further optimization can be achieved)
