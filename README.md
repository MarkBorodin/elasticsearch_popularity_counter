## popularity_counter for elasticsearch  

#### This counts the number of times a specific document was returned by elastixsearch (a document in elastixsearch is a model object in django). Based on this, it is possible to sort suggestions by popularity on the front end.
This addition does not change the database, it only adds a field to the document in elastixsearch

Installation:

* Create app "popularity_counter" and add to this folder files from repo:  
https://github.com/MarkBorodin/elasticsearch_popularity_counter  

* Add 'popularity_counter' to INSTALLED_APPS in settings.py:
```
INSTALLED_APPS = [
    ...
    'popularity_counter',
    ...
]
```

* Add middleware at the very end of the list MIDDLEWARE in settings.py:  
```
MIDDLEWARE = [
    ...
    'popularity_counter.middleware.ElasticsearchPopularityMiddleware',
]
```

* In the document for which you need to track popularity, add a field:
(documents.py)
```
popularity_counter = fields.IntegerField(attr='popularity_counter')
```
for example:  
```
@registry.register_document
class ArticleDocument(Document):
    ...
    popularity_counter = fields.IntegerField(attr='popularity_counter')
    ...
```

In the serializers for which you need to track popularity, add 'popularity_counter' to 'fields':  
(serializers.py)
for example:  
```
class ArticleDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ArticleDocument
        fields = ('title', 'category', 'content', 'id', 'popularity_counter')
```
