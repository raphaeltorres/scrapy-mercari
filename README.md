# scrapy-mercari
Scrape mercari infinite scroll

# Installation
Clone Repo
 > git clone https://github.com/raphaeltorres/scrapy-mercari.git

 Create virtualenv
 > virtualenv -p python3 mercari

 Activate virtualenv
 > source mercari/bin/activate

 Install scrapy
 > pip install -r requirements.txt

Scrape Products
> scrapy crawl products

> scrapy crawl products -o products.csv -t csv | CSV Format

> scrapy crawl products -o product.json | JSON Format

Scrape Products using keywords
> scrapy crawl search -a keyword="kyrie5" -o kyrie5.csv

Scrape Seller reviews
> scrapy crawl seller -o seller.csv -t csv
