import scrapy
import json


class ProductsSpider(scrapy.Spider):
    def get_brand_ids():
        brand_ids = [4239, 2766, 4578, 1243, 319, 6483, 1400, 10954, 7160]
        for id in brand_ids:
            yield id

    name = 'products'
    base_url = 'https://www.mercari.com'
    api_url = 'https://www.mercari.com/v1/api'
    product_url = 'https://www.mercari.com/us/item/'
    offset = 20
    count = 0
    brand_ids = get_brand_ids()
    request_body = {
        "operationName": "brandCategoryQuery",
        "variables": {
            "criteria": {
                "offset": offset,
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
        else:
            try:
                brand_id = self.brand_ids.next()
                self.offset = 20
                self.request_body['variables']['criteria']['brandIds'] = []
                self.request_body['variables']['criteria']['brandIds'].append(brand_id)
                self.request_body['variables']['brandId'] = brand_id
                self.request_body['variables']['criteria']['offset'] = self.offset
                yield self.mercari_scapy_request()
            except StopIteration:
                pass

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
