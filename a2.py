'''
COMP9321 2019 Term 1 Assignment Two Code Template
Student Name: Hang Zhang
Student ID: z5153042
'''
import sqlite3,os,time,json,requests
import flask,flask_restplus

from time import strftime
# from flask import Flask
from flask import request
# from flask_restplus import Resource, Api
from flask_restplus import fields
from flask_restplus import inputs
from flask_restplus import reqparse



def create_db(db_file):
    '''
    uase this function to create a db, don't change the name of this function.
    db_file: Your database's name.
    '''
    try:
    	conn = sqlite3.connect(db_file)
    	# print(sqlite3.version)
    except sqlite3.Error as e:
    	print(e) 
    
    return conn
'''
Put your API code below. No certain requriement about the function name as long as it works.
'''

connection = create_db('data.db')
# print('database create successfully\n')
cur_ = connection.cursor()
cur_.execute('create table if not exists collections \
	(collection_id,indicator_value,creation_time, PRIMARY KEY (collection_id))')
cur_.execute('create table if not exists entities \
	(collection_id,country,date,value,PRIMARY KEY (collection_id,country,date),\
	FOREIGN KEY (collection_id) REFERENCES collections (collection_id))')
cur_.close()
# cur.execute("SHOW TABLES")

def query(cur,query):
	# cur = connection.cursor()
	cur.execute(query)
	rows = cur.fetchall()
	return rows

def insert(cur,query,var,conn1):
	# cur = connection.cursor()
	cur.execute(query,var)
	conn1.commit()

def delete(cur,query):
	# cur = connection.cursor()
	cur.execute(query)

def update(cur,query,var):
	# cur = connection.cursor()
	cur.execute(query,var)
	rows = cur.fetchall()
	return rows

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

app = flask.Flask(__name__)
api = flask_restplus.Api(app,
		  default = "Collections",
		  title = "Data Service for World Bank Economic Indicators.",
		  description = "World Bank Economic Indicators API")

indicator_model = api.model('Indicator', { 'indicator_id' : fields.String })
@api.route('/collections')

class POST_GET(flask_restplus.Resource):
	@api.response(200, 'Collection Has Been Imported Already, Please Check and Reinput.')	
	@api.response(201, 'Collection Created Successfully')
	@api.response(400, 'Bad Request')
	@api.response(404, 'Indicator_id Not Found in page')
	@api.doc(description = "Import a collection from the data service (Question 1)")
	@api.expect(indicator_model, validate = True)
	# Question 1
	def post(self):

		conn1 = sqlite3.connect('data.db')
		indicator = flask.request.json
		print(indicator)
		cur = conn1.cursor()

		if not indicator['indicator_id']:
			return { 'message': 'Missing indicator_id'}, 400

		indicator_id = indicator['indicator_id']


		url = "http://api.worldbank.org/v2/countries/all/indicators/"+indicator_id+"?date=2013:2018&format=json"
		response = requests.get(url)
		jsontxt = response.json()

		if response.status_code != 200 or len(jsontxt) < 2:
			return {'message': 'indicator_id {} is not available'.format(indicator_id)}, 404

		# Set system timezone and format
		os.environ['TZ'] = 'AEST-10AEDT-11,M10.5.0,M3.5.0'
		creation_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")

		response_body = { 
						"location" : "/collections/"+indicator_id, 
						"collection_id" : indicator_id,  
						"creation_time": creation_time,
						"indicator" : indicator_id
					}

		query_txt = 'select * from collections where collection_id =' +'"'+ indicator_id +'"'
		rows = query(cur,query_txt)
		# print(rows)
		if len(rows) > 0:
			return response_body, 200
		collection = (indicator_id,"GDP (current US$)", creation_time)
		query_txt = 'insert into  collections values (?,?,?)'

		insert(cur,query_txt,collection,conn1)
		for i in range(1,3):
			response = requests.get(url+'&page='+str(i))
			# entities_num = len(response.json()[1])
			entities = response.json()[1]
			for j in range(len(response.json()[1])):
				data = (indicator_id,entities[j]["country"]["value"],entities[j]["date"],entities[j]["value"])
				query_txt = 'insert into  entities values (?,?,?,?)'
				insert(cur,query_txt,data,conn1)

		cur.close()
		return response_body, 201

	# question 3
	@api.response(200, 'Retrieve Collections Successfully')
	@api.doc(description = "Retrieve the list of available collections (Question 3)")
	def get(self):

		conn1 = sqlite3.connect('data.db')
		# indicator = flask.request.json
		cur = conn1.cursor()

		response_body = []
		query_txt = 'select * from collections'
		rows = query(cur,query_txt)

		if len(rows) < 1:
			return {"message": "No record in Collection now"}, 200

		# print(rows)
		row_id= [i[0] for i in rows]
		row_time = [i[2] for i in rows]
		# print(row_id)
		for i in row_id:
			collec_index = 0
			collec_info = {}
			query_txt = 'select * from collections where collection_id = '+'"'+i+'"'
			rows = query(cur,query_txt)
			# print(rows)
			# for j in rows:
			collec_info["location"] = "/collections/"+i
			collec_info["collection_id"] = i
			collec_info["creation_time"] = row_time[collec_index]
			collec_info["indicator"] = i
			# print(collec_info)
			response_body.append(collec_info)
			collec_index += 1
		return response_body, 200

@api.route('/collections/<string:collection_id>')
@api.param('collection_id', 'The Collection identifier')
class Remove(flask_restplus.Resource):
	# question 2
	@api.response(200, 'Collection Removed Successfully')
	@api.response(404, 'Collection Not Found')
	@api.doc(description = "Deleting a collection with the data service (Question 2)")
	def delete(self, collection_id):
		conn1 = sqlite3.connect('data.db')
		cur = conn1.cursor()

		query_txt = 'select * from collections where collection_id =' +'"'+ collection_id +'"'
		rows = query(cur,query_txt)
		# print(rows)
		if len(rows) < 1:
			return {"message": "Collection {} doesn't exist".format(collection_id)}, 404
		query_txt = 'delete from collections where collection_id = ' +'"' +collection_id +'"'
		# print(query_txt)
		delete(cur,query_txt)
		conn1.commit() # important

		query_txt = 'delete from entities where collection_id = ' +'"' +collection_id +'"'
		# print(query_txt)
		delete(cur,query_txt)
		conn1.commit() # important

		return {"message": "Collection = {} is removed from the database!".format(collection_id)}, 200

	# question 4
	@api.response(200, 'Collection Retrived Successfully')
	@api.response(404, 'Collection Not Found')
	@api.doc(description = "Retrieve a collection (Question 4)")
	def get(self, collection_id):
		conn1 = sqlite3.connect('data.db')
		cur = conn1.cursor()

		query_txt = 'select * from collections where collection_id =' +'"'+ collection_id +'"'
		rows = query(cur,query_txt)
		# print(rows)
		if len(rows) < 1:
			return {"message": "Collection {} doesn't exist".format(collection_id)}, 404

		# query_txt = 'select * from collections where collection_id =' +'"'+ collection_id +'"'
		# rows = query(cur,query_txt)
		# print(rows)
		row_id= rows[0][0]
		row_time = rows[0][2]
		response_body = {}
		response_body["collection_id"] = rows[0][0]
		response_body["indicator"] = rows[0][0]
		response_body["indicator_value"] = rows[0][1]
		response_body["creation_time"] = rows[0][2]
		response_body["entries"] = []


		query_txt = 'select e.country,e.date,e.value from collections c,entities e where c.collection_id = e.collection_id and c.collection_id =' + '"' +collection_id + '"'
		rows_ = query(cur,query_txt)
		# print(rows_,len(rows_))
		for i in rows_:
			country ={}
			country["country"] = i[0]
			country["date"] = i[1]
			country["value"] = i[2]
			response_body["entries"].append(country)

		return response_body, 200

@api.route('/collections/<string:collection_id>/<string:year>/<string:country>')
@api.param('collection_id', 'The Collection identifier')
@api.param('year', 'The year')
@api.param('country', 'The country')
class Retrieve(flask_restplus.Resource):
	# question 5
	@api.response(200, 'Indicator Value Found Successfully')
	@api.response(404, 'Parameters Not Available')
	@api.doc(description = "Retrieve economic indicator value for given country and a year (Question 5)")
	def get(self, collection_id, year, country):
		conn1 = sqlite3.connect('data.db')
		cur = conn1.cursor()

		query_txt = 'select * from collections where collection_id =' +'"'+ collection_id +'"'
		rows = query(cur,query_txt)
		# print(rows)
		if len(rows) < 1:
			return {"message": "Collection {} doesn't exist".format(collection_id)}, 404
		response_body = {}
		query_txt = 'select c.collection_id,e.country,e.date,e.value from collections c,entities e where (c.collection_id = e.collection_id and e.date =' + '"' + year + '" and e.country = ' + '"' + country +'"'+ 'and c.collection_id =' + '"' +collection_id+ '")'
		print(query_txt)
		rows = query(cur,query_txt)
		print(rows,len(rows),'\n')
		if len(rows) < 1:
			return {"message": "No record in database of country: '{}', year: '{}' and collection ID: '{}', please check and reinput".format(country,year,collection_id)}, 404

		response_body["collection_id"] = rows[0][0]
		response_body["indicator"] = rows[0][0]
		response_body["country"] = rows[0][1]
		response_body["year"] = rows[0][2]
		response_body["value"] = rows[0][3]

		if response_body["value"] == None:
			return {"message": "Parameters are not available"}, 404
		return response_body, 200


parser = api.parser()
parser.add_argument('q', type=str, help='top<N> or bottom<N>', location='args')
@api.route('/collections/<string:collection_id>/<string:year>')
class Retrieve_sort(flask_restplus.Resource):
	# question 6
	@api.response(200, "Retrieve Indicator Values Successfully")
	@api.response(400, "Bad Request")
	@api.response(404, "Parameters Not Available")
	@api.expect(parser, validate = True)
	@api.doc(description = "Retrieve top/bottom economic indicator values for a given year (Question 6)")
	def get(self, collection_id, year):
		conn1 = sqlite3.connect('data.db')
		cur = conn1.cursor()

		query_txt = 'select * from collections where collection_id =' +'"'+ collection_id +'"'
		rows = query(cur,query_txt)

		# print(rows)
		if len(rows) < 1:
			return {"message": "Collection {} doesn't exist".format(collection_id)}, 404

		query_txt = 'select c.collection_id,c.indicator_value,e.country,e.date,e.value from collections c,entities e where (c.collection_id = e.collection_id and e.date =' + '"' + year + '")'
		# print(query_txt)
		rows_ = query(cur,query_txt)
		rows = []

		print(rows_)
		for i in rows_:
			if i[4] != None:
				rows.append(i)
		print(rows)

		q = parser.parse_args()
		# print(q)

		if len(rows) < 1:
			return {"message": "Query {} not available because of null values".format(q['q'])}, 400

		response_body = {}

		response_body["collection_id"] = collection_id
		response_body["indicator"] = rows[0][1]
		

		

		if q['q'] == None:
			temp = []
			for i in rows:
				temp_country = {}
				temp_country["country"] = i[2]
				temp_country["date"] = i[3]
				temp_country["value"] = i[4]
				temp.append(temp_country)
			response_body["entries"] = temp
			return response_body, 200

		order = 0
		count = 0
		if q['q'][0:3].lower() != 'top'and q['q'][0:6].lower() != 'bottom':
			return {"message": "Query {} not available".format(q['q'])}, 400
		# print('some problems')

		if q['q'][0:3].lower() == 'top':
			order = 1
			# print('some problems1')

			if not RepresentsInt(q['q'][3:]):
				return {"message": "Query {} not available".format(q['q'])}, 400
			count = int(q['q'][3:])
			# print (q['q'],q['q'][3:],type(q['q'][3:]),isinstance(q['q'][3:], int))
		# print('some problems11')
		if q['q'][0:6].lower() == 'bottom':
			order = -1
			# print('some problems111')
			if not RepresentsInt(q['q'][6:]):
				return {"message": "Query {} not available".format(q['q'])}, 400
			count = int(q['q'][6:])

		if count < 1 or count > 100:
			return {"message": "<N> {} out of range".format(count)}, 400

		if count > len(rows):
			count = len(rows)
		if order == 1:
			rows = sorted(rows,key = lambda x: x[4], reverse = True)
		elif order == -1:
			rows = sorted(rows,key = lambda x: x[4], reverse = False)

		temp = []
		# print(rows)
		for i in rows[:count]:
			temp_country = {}
			temp_country["country"] = i[2]
			temp_country["date"] = i[3]
			temp_country["value"] = i[4]
			temp.append(temp_country)
		response_body["entries"] = temp

		return response_body, 200





'''
create table if not exists entities \
	(collection_id,country,date,value,PRIMARY KEY (collection_id,country,date),\
	FOREIGN KEY (collection_id) REFERENCES collections (collection_id))')

create table if not exists collections \
	(collection_id,indicator_value,creation_time, PRIMARY KEY (collection_id))')

'''



if __name__ == '__main__':
	app.run(debug = True)
