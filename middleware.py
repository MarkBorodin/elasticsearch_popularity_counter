import datetime
import json
from elasticsearch import Elasticsearch
from django.utils.deprecation import MiddlewareMixin


class ElasticsearchPopularityMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if 'application/json' in response['Content-Type']:
            data = response.content.decode('utf-8')
            self.update_popularity_counters(data)
        return response

    def update_popularity_counters(self, data):
        search_results = json.loads(data)
        document_hits = search_results.get('results', [])
        if document_hits:
            self.increment_counters(document_hits)
        else:
            options = [option['options'] for option in search_results[list(search_results.keys())[0]]]
            for option in options:
                for result in option:
                    document_hits.append(result['_source'])
            if document_hits:
                self.increment_counters(document_hits)

    def increment_counters(self, document_hits):
        try:
            es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])
            for hit in document_hits:
                document_id = hit['id']
                if 'popularity_counter' not in hit:
                    es.update(index='articles', id=document_id, body={'doc': {'popularity_counter': 1}})
                else:
                    es.update(index='articles', id=document_id, body={
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
