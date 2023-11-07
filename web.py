from flask import Flask, render_template, jsonify, request, Response
from lxml import html
import requests
from rdflib import Graph
import json
import urllib.parse
app=Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route('/_scrape' ,methods=['GET'])
def scrape():
    books=list()
    book=dict()
    site=requests.get('https://en.wikipedia.org/wiki/List_of_best-selling_books')
    tree = html.fromstring(site.content)
    data = tree.xpath('//div[@class="mw-parser-output"]/table[1]/tbody/tr[position() >= 2 and not(position() > 4)]/td[position() =1 or position() =4]/descendant-or-self::*/text()')
    del data[3:6]
    id=1
    for index in range(0,5,2):
        book={"id":id ,'title':data[index], 'year':int(data[index+1])}
        id+=1
        books.append(book)
    return jsonify(books)
@app.route('/_rdf', methods=['POST'])
def rdf():
    if request.method == 'POST':
        data = request.get_json()
        data[-1]['id']=len(data)
        headers={"Content-type": 'application/x-www-form-urlencoded'}
        adresa='http://localhost:8080/rdf4j-server/repositories/grafexamen/statements?update='
        for item in data:

            interogare=f"""PREFIX : <http://grama.ro#> INSERT DATA {{graph :graf{item['id']} {{:Carte{item['id']} :lansatIn :{item['year']}; :title "{item['title']}"; a :Book}}}}"""
            interogare=urllib.parse.quote(interogare)
            url=adresa+interogare
            requests.post(url=url, headers=headers)
        graph=Graph()
        qres = graph.query(
            """
            PREFIX : <http://grama.ro#>
            SELECT ?x ?y ?z
            WHERE {
            SERVICE <http://localhost:8080/rdf4j-server/repositories/grafexamen> {
            ?x ?y ?z .
            }
            }
            """
                            )
        item=dict()
        books=list()
        index=0
        for row in qres:
            if str(row.y) == 'http://grama.ro#lansatIn':
                item['year']=str(row.z).split('#')[1]
            elif str(row.y) == 'http://grama.ro#title':
                item['title']=str(row.z)
            if 'year' in item and 'title' in item:
                index+=1
                item['id']=index
                books.append(item)
                item=dict()
        return jsonify(books)

@app.route('/_json_server', methods=['POST'])
def json_server():
    if request.method == 'POST':
        adresa='http://localhost:4000/books'
        data = request.get_json()
        for item in data:
            item['id']+=1
        headers = {'Content-type': 'application/json'}
        for item in data:
                requests.post(adresa, json=item, headers=headers)
        data=requests.get(adresa).content
        return Response(data, mimetype='application/json')
@app.route('/_delete_json_server', methods=['POST'])
def delete_json_server():
    if request.method == 'POST':
        adresa='http://localhost:4000/books'
        title=request.get_data(as_text=True)
        title=title.replace('%20', ' ')
        data=requests.get(f'{adresa}?{title}')
        data=json.loads(data.content)
        id=data[0]['id']
        requests.delete(f'{adresa}/{id}')
        data=requests.get(adresa).content
        return Response(data, mimetype='application/json')
