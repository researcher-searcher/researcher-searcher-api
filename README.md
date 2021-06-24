# researcher-searcher-api

API for Researcher Searcher

### local dev

https://pypi.org/project/fastapi/

uvicorn app.main:app --reload

pip install spacy-universal-sentence-encoder

### build

Create image:

`docker-compose build`

Create .env file

```
GRAPH_HOST=
GRAPH_USER=neo4j
GRAPH_PASSWORD=
GRAPH_HTTP_PORT=
GRAPH_BOLT_PORT=

ELASTIC_VERSION=7.13.2
ELASTIC_HOST=
ELASTIC_PORT=
ELASTIC_USER=elastic
ELASTIC_PASSWORD=

LOGSTASH_HOST=
LOGSTASH_PORT=

API_PORT=
NAME=
```

Create container

`docker-compose up -d`

### todo

Response model - https://fastapi.tiangolo.com/tutorial/response-model/

### example queries

```
curl -XGET 'http://localhost:8000/search/?method=vec&query=nematode'
```

```
curl -XGET 'http://localhost:8000/search/?method=full&query=Blood%20Donation.%20Organ%20Donation%20and%20Transplantation.%20Therapeutics.%20Data%20Driven%20Transfusion%20Practice.%20Transfusion%20and%20Transplantation%20Transmitted%20Infections'
```

##### Does a bio find the person

- e.g. https://research-information.bris.ac.uk/en/persons/tim-cole-cole

```
http://localhost:8000/search/?query=Tim%20has%20wide%20ranging%20interests%20in%20social%20and%20environmental%20histories,%20historical%20geographies%20and%20digital%20humanities%20and%20also%20works%20within%20the%20creative%20economy.%20His%20core%20research%20has%20focused%20in%20the%20main%20on%20Holocaust%20landscapes%20-%20both%20historical%20and%20memory%20landscapes%20-%20writing%20books%20on%20Holocaust%20representation%20(Images%20of%20the%20Holocaust/Selling%20the%20Holocaust,%201999),%20the%20spatiality%20of%20ghettorization%20in%20Budapest%20(Holocaust%20City,%202003),%20social%20histories%20of%20the%20Hungarian%20Holocaust%20(Traces%20of%20the%20Holocaust,%202011)%20and%20the%20spatiality%20of%20survival%20(Holocaust%20Landscapes,%202016)%20as%20well%20as%20co-editing%20a%20collection%20of%20essays%20emerging%20from%20an%20interdisciplinary%20digital%20humanities%20project%20he%20co-led%20(Geographies%20of%20the%20Holocaust,%202015).%20Alongside%20this%20research,%20Tim%20has%20also%20developed%20interests%20in%20environmental%20history,%20being%20a%20co-editor%20of%20a%20study%20of%20military%20landscapes%20(Militarised%20Landscapes,%202010)%20and%20now%20working%20on%20a%20new%20book%20that%20explores%20social,%20cultural,%20landscape%20and%20environmental%20change%20in%20post-war%20Britain%20(About%20Britain).&method=person
```

### notes

Need to include option to return all supporting info, e.g. the sentences and scores that matched the query.

How do results compare when searching via sentence vectors compared to using single doc?
- can search against person vector directly or sentences-output-person
- compare analysing each sentence of query document to using whole thing 
- why doesn't a search using exact text in index return the matching people first, e.g. test_text3 from MPresto