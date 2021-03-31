# researcher-searcher-api
API for Researcher Searcher

python -m spacy download en_core_web_lg

### local dev

https://pypi.org/project/fastapi/

uvicorn app.main:app --reload

### build

docker-compose build

### todo

Response model - https://fastapi.tiangolo.com/tutorial/response-model/

### example queries

```
curl -XGET 'http://localhost:8000/search/?method=vec&query=nematode'
```

```
curl -XGET 'http://localhost:8000/search/?method=full&query=Blood%20Donation.%20Organ%20Donation%20and%20Transplantation.%20Therapeutics.%20Data%20Driven%20Transfusion%20Practice.%20Transfusion%20and%20Transplantation%20Transmitted%20Infections'
```

### notes

Need to include option to return all supporting info, e.g. the sentences and scores that matched the query.

