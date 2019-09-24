import scrapy
import json


class ProductsSpider(scrapy.Spider):
    name = 'products'
    api_url = 'https://www.mercari.com/v1/api'
    offset = 20
    count = 0
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
        yield scrapy.Request(
            self.api_url,
            method="POST",
            body=json.dumps(self.request_body),
            headers={'Content-Type': 'application/json; charset=UTF-8'}
        )

    def parse(self, response):
        data = json.loads(response.text)
        if data['data']['search']['itemsList']:
            item_list = data['data']['search']['itemsList']
            for row in item_list:
                self.count = self.count + 1
                yield {
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'original_price': row['originalPrice'],
                    'count': self.count
                }

            self.offset = self.offset + 20
            yield scrapy.Request(
                self.api_url,
                method="POST",
                body=json.dumps(self.request_body),
                headers={'Content-Type': 'application/json; charset=UTF-8'},
                callback=self.parse
            )
