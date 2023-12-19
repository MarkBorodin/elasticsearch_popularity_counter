import datetime
import json
from elasticsearch import Elasticsearch
from django.utils.deprecation import MiddlewareMixin
from rest_framework.viewsets import ReadOnlyModelViewSet


class ElasticsearchPopularityMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 'application/json' in response['Content-Type']:
            data = response.content.decode('utf-8')
            index_name = self.get_elasticsearch_index(request)
            self.update_popularity_counters(data, index_name)
        return response

    def update_popularity_counters(self, data, index_name):
        search_results = json.loads(data)
        document_hits = search_results.get('results', [])
        if document_hits:
            self.increment_counters(document_hits, index_name)
        else:
            options = [option['options'] for option in search_results[list(search_results.keys())[0]]]
            for option in options:
                for result in option:
                    document_hits.append(result['_source'])
            if document_hits:
                self.increment_counters(document_hits, index_name)

    def increment_counters(self, document_hits, index_name):
        try:
            es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
            for hit in document_hits:
                document_id = hit['id']
                if 'popularity_counter' not in hit:
                    es.update(index=index_name, id=document_id, body={'doc': {'popularity_counter': 1}})
                else:
                    es.update(index=index_name, id=document_id, body={
                            "script": {
                                "source": "if (ctx._source.containsKey(params.field)) { ctx._source[params.field] = (ctx._source[params.field] ?: 0) + params.increment } else { ctx._source[params.field] = params.increment }",
                                "params": {
                                    "field": "popularity_counter",
                                    "increment": 1
                                }
                            }
                        }
                    )
        except Exception as e:
            with open('popularity_counter/ElasticsearchPopularity.log', 'a') as f:
                f.write(f'\n {datetime.datetime.now()}: {e}')

    def get_elasticsearch_index(self, request):
        path = str(request.path)
        index = None
        if path.endswith('/'):
            class_url = path.split(sep='/')[-2]
            if class_url == 'shop-categories':
                index = "shopcategory"
            elif class_url == 'shop-subcategories':
                index = "shopsubcategory"
            elif class_url == 'shop-products':
                index = "shopproduct"
            elif class_url == 'shop-product-attributes':
                index = "shopproductattribute"
            elif class_url == 'shop-product-texts':
                index = "shopproducttext"
            elif class_url == 'shop-product-metas':
                index = "shopproductmeta"
            elif class_url == 'shop-product-variation':
                index = "shopproductvariation"
            return index
