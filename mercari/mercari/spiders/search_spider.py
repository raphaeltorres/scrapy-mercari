import scrapy
import json


class SearchSpider(scrapy.Spider):
    name = 'search'

    def __init__(self, keyword='', **kwargs):
        self.base_url = 'https://www.mercari.com'
        self.api_url = 'https://www.mercari.com/v1/api'
        self.product_url = 'https://www.mercari.com/us/item/'
        self.offset = 20
        self.count = 0

        self.request_body = {
           "operationName":"searchQuery",
           "variables":{
              "criteria":{
                 "offset": self.offset,
                 "sortBy": 0,
                 "length": 30,
                 "query": keyword,
                 "itemConditions":[],
                 "shippingPayerIds":[],
                 "sizeGroupIds":[],
                 "sizeIds":[],
                 "itemStatuses":[],
                 "customFacets":[],
                 "facets":[2],
                 "searchId":""
              },
              "categoryId":0
           },
           "query":"query searchQuery($criteria: SearchInput!) {\n  search(criteria: $criteria) {\n    itemsList {\n      id\n      name\n      status\n      description\n      originalPrice\n      shippingPayer {\n        id\n        name\n        __typename\n      }\n      photos {\n        thumbnail\n        __typename\n      }\n      seller {\n        sellerId: id\n        photo\n        ratings {\n          sellerRatingCount: count\n          sellerRatingAverage: average\n          __typename\n        }\n        __typename\n      }\n      price\n      itemDecoration {\n        id\n        imageUrl\n        __typename\n      }\n      brand {\n        id\n        name\n        __typename\n      }\n      itemSize {\n        id\n        name\n        __typename\n      }\n      itemCondition {\n        id\n        name\n        __typename\n      }\n      itemCategory {\n        id\n        name\n        __typename\n      }\n      customFacetsList {\n        facetName\n        value\n        __typename\n      }\n      __typename\n    }\n    page {\n      offset\n      __typename\n    }\n    count\n    facetsList {\n      criteria {\n        brandIdsList\n        categoryList {\n          id\n          name\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    searchId\n    parsedQuery\n    metadata {\n      queryAfterRemoval\n      __typename\n    }\n    latency {\n      searchService\n      algolia\n      qupService\n      rerankService\n      clusterLatencyMap {\n        clusterName\n        latency\n        __typename\n      }\n      __typename\n    }\n    criteria {\n      query\n      sortBy\n      categoryIds\n      brandIds\n      itemStatuses\n      itemConditions\n      shippingPayerIds\n      sizeGroupIds\n      sizeIds\n      maxPrice\n      minPrice\n      __typename\n    }\n    __typename\n  }\n}\n"
        }
        super().__init__(**kwargs)

    def start_requests(self):
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
        if data['data']['search']['itemsList']:
            item_list = data['data']['search']['itemsList']
            for row in item_list:
                self.count = self.count + 1
                request = scrapy.Request(
                    '{}{}/'.format(self.product_url, row['id']),
                    method="GET",
                    callback=self.parse_page2,
                    cb_kwargs=dict(main_url=response.url)
                )
                request.cb_kwargs['data'] = row
                yield request

            self.offset = self.offset + 20
            self.request_body['variables']['criteria']['offset'] = self.offset
            yield self.mercari_scapy_request()

    def parse_page2(self, response, main_url, data):
        div_seller_path = '//div[contains(@class, "Seller__Left")]//a'
        seller_name_path = '//p[contains(@class, "ProfileBar__Name")]/text()'
        seller_review_path = '//p[contains(@class, "Seller__ReviewText")]//span/text()'
        items_listed_path = '//div[contains(@class, "ProfileBar__NumSellContainer")]//p//span/text()'
        shipping_path = '//p[contains(@class, "Text__ProductText")]/text()'

        seller_profile = response.xpath(div_seller_path)
        seller_name = seller_profile.xpath(seller_name_path).get()
        seller_url = seller_profile.xpath('@href').get()
        num_seller_reviews = seller_profile.xpath(seller_review_path).get()
        num_seller_items_listed = seller_profile.xpath(items_listed_path).extract_first()
        num_seller_sales = seller_profile.xpath(items_listed_path).getall()[-1]
        shipping = response.xpath(shipping_path).getall()[1].split(' ')
        image_urls = []

        for img in data['photos']:
            image_url = img['thumbnail']
            image_urls.append(image_url.split('?')[0])

        yield {
            'product_id': data['id'],
            'product_title': data['name'],
            'product_price': data['price'],
            'product_url': '{}{}/'.format(self.product_url, data['id']),
            'product_condition': data['itemCondition']['name'],
            'product_brand': data['brand']['name'],
            'product_description': data['description'],
            'shipping_cost': shipping[0],
            'shipping_origin': shipping[-1],
            'seller_name': seller_name,
            'seller_url': '{}{}'.format(self.base_url, seller_url),
            'num_seller_reviews': int(num_seller_reviews),
            'num_seller_items_listed': int(num_seller_items_listed),
            'num_seller_sales': int(num_seller_sales),
            'image_urls': image_urls
        }
