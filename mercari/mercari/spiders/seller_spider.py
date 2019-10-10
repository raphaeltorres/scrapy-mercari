import scrapy
import json
import csv
import fnmatch
import os
from scrapy import Selector

class SellerSpider(scrapy.Spider):
    name = 'seller'
    base_url = 'https://www.mercari.com'
    api_url = 'https://www.mercari.com/v1/api'
    mercari_sellers = {}
    seller_reviews = []

    request_body = {
        "operationName": "brandCategoryQuery",
        "variables": {
            "criteria": {
                "offset": 20,
                "sortBy": 0,
                "length": 30,
                "brandIds": [3908],
                "itemConditions": [],
                "shippingPayerIds": [],
                "sizeGroupIds": [],
                "sizeIds": [],
                "itemStatuses": [],
                "customFacets": [],
                "facets": [1, 2],
                "searchId": ""
            },
            "categoryId": 0,
            "brandId": 3908
        },
        "query": "query brandCategoryQuery($criteria: SearchInput!, $brandId: Int!, $categoryId: Int!) { search(criteria: $criteria) {\n    itemsList {\n      id\n      name\n      status\n      description\n      originalPrice\n      shippingPayer {\n        id\n        name\n        __typename\n      }\n      photos {\n        thumbnail\n        __typename\n      }\n      seller {\n        sellerId: id\n        photo\n        ratings {\n          sellerRatingCount: count\n          sellerRatingAverage: average\n          __typename\n        }\n        __typename\n      }\n      price\n      itemDecoration {\n        id\n        imageUrl\n        __typename\n      }\n      brand {\n        id\n        name\n        __typename\n      }\n      itemSize {\n        id\n        name\n        __typename\n      }\n      itemCondition {\n        id\n        name\n        __typename\n      }\n      itemCategory {\n        id\n        name\n        __typename\n      }\n      customFacetsList {\n        facetName\n        value\n        __typename\n      }\n      __typename\n    }\n    page {\n      offset\n      __typename\n    }\n    facetsList {\n      criteria {\n        categoryList {\n          id\n          name\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    count\n    __typename\n  }\n  master {\n    itemBrands(id: $brandId) {\n      name\n      __typename\n    }\n    __typename\n  }\n  categories(id: $categoryId) {\n    title\n    categoryLevels {\n      level\n      selected {\n        name\n        id\n        __typename\n      }\n      categoryList {\n        name\n        id\n        displayOrder\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  keywords(categoryId: $categoryId, brandId: $brandId) {\n    categoryId\n    brandId\n    displayName\n    pageUri\n    __typename\n  }\n  relatedShopItems(brandId: $brandId, categoryId: $categoryId) {\n    brandId\n    categoryId\n    pageUri\n    pageTitle\n    __typename\n  }\n}\n"}

    def start_requests(self):
        for file in os.listdir('.'):
            if fnmatch.fnmatch(file, '*.csv'):
                if 'seller' not in file:
                    with open(file, mode='r') as csv_file:
                        csv_reader = csv.DictReader(csv_file)
                        line_count = 0
                        for row in csv_reader:
                            if line_count == 0:
                                line_count += 1
                            seller_id = row['seller_url'][:-1].split('/')[-1]
                            if seller_id.isdigit():
                                if seller_id not in self.mercari_sellers:
                                    self.mercari_sellers[seller_id] = {
                                        'seller_url': row['seller_url'],
                                        'seller_id': seller_id
                                    }
                            line_count += 1
        yield self.mercari_scapy_request()


    def mercari_scapy_request(self):
        return scrapy.Request(
                self.api_url,
                method="POST",
                body=json.dumps(self.request_body),
                headers={'Content-Type': 'application/json; charset=UTF-8'},
                callback=self.parse
            )

    def parse(self, response):
        data = json.loads(response.text)
        for row in self.mercari_sellers:
            self.seller_reviews = []
            seller_url = self.mercari_sellers[row]['seller_url']
            request = scrapy.Request(
                seller_url,
                method="GET",
                callback=self.parse_seller_page,
                cb_kwargs=dict(main_url=response.url)
            )
            yield request

    def parse_seller_page(self, response, main_url):
        div_seller_path = '//ul[contains(@class, "user-status")]//li//span/text()'
        seller_name_path = '//div[contains(@class, "user-name-container")]/a/h2/text()'
        seller_review_path = '//div[contains(@class, "user-page-inner")]/a/@href'

        seller_profile = response.xpath(div_seller_path).getall()
        seller_name = response.xpath(seller_name_path).get()
        seller_review_url = response.xpath(seller_review_path).get()

        review_url = '{}{}'.format(self.base_url, seller_review_url)

        seller_data = {
            'seller_name': seller_name,
            'member_since': seller_profile[1],
            'seller_status': seller_profile[-1],
            'seller_url': response.url,
            'review_url': review_url
        }

        request = scrapy.Request(
            review_url,
            method="GET",
            callback=self.seller_review_page,
            cb_kwargs=dict(
                main_url=response.url,
                data=seller_data,
                seller_reviews=[]
            )
        )
        yield request


    def seller_review_page(self, response, main_url, data, seller_reviews):
        next_page_url = response.css('li.pager-next > a::attr(href)').extract_first()

        seller_review = []

        for row in response.css('.review-item'):
            reviewer_name = row.css('.review-item-right-column > a > div').xpath('text()').get()
            review_date = row.css('.review-item-right-column > div > time').xpath('text()').get()
            review_desc = row.css('.review-item-right-column > p > span').xpath('text()').get()
            if reviewer_name and reviewer_name != '':
                seller_review.append({
                    'reviewer_name': reviewer_name.strip(),
                    'review_date': review_date.strip(),
                    'description': review_desc.strip()
                })

        reviews = [*seller_review, *seller_reviews]

        if next_page_url:
            next_page_req = scrapy.Request(
                '{}{}'.format(self.base_url, next_page_url),
                method="GET",
                callback=self.seller_review_page,
                cb_kwargs=dict(
                    main_url=response.url,
                    data=data,
                    seller_reviews=reviews
                )
            )
            next_page_req.cb_kwargs['data'] = data
            yield next_page_req
        else:
            yield {
                'seller_name': data['seller_name'],
                'seller_url': data['seller_url'],
                'seller_status': data['seller_status'],
                'member_since': data['member_since'],
                'review_url': data['review_url'],
                'reviews': reviews
            }
