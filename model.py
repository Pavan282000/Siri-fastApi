from fastapi import FastAPI
from typing import Optional, Any, List
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from typing import List, Optional


import uvicorn as uvicorn
import numpy as np


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphdb = GraphDatabase.driver(uri="neo4j+s://f951f243.databases.neo4j.io", auth=("neo4j", "08_xJvvomlHaYsaUnUfXiM8hFQmvRijMzPDed63f_y0"), max_connection_lifetime=1)
session = graphdb.session()

@app.post('/addParentNode',tags=["Organisation"])
async def addParentNode():
    q2 = '''CREATE (ParentNode: Survey{name:"Survey"}) '''
    q3 = """ CREATE (d: Dimension{name:"Dimension"})"""
    result = session.run(q2)
    session.run(q3)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("Parent node Created")

@app.post('/postOrganisation/{name}',tags=["Organisation"])
async def organisationDetails(name,sector):
    q2 = '''MATCH(C: Survey{name:"Survey"})
                CREATE (C) -[:hasOrganisation]->(O: Organisation{name:$name,sector:$sector})'''
    x={"name":name,"sector":sector}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("Organisation node added")




@app.get('/getCompanies' ,tags=["Organisation"])
async def getComapnies():

    q2 = '''MATCH (n:Organisation) RETURN  (n.name) as Organisations ,(n.sector) as Sector  ORDER BY n.name LIMIT 5'''
    result = session.run(q2)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)


##Fetching the models available

@app.get('/getModels' ,tags=["Models"])
async def getModels():
    q2 = '''MATCH (n:Model) RETURN  collect(n) as Models '''
    result = session.run(q2)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)

class Model(BaseModel):
    name: str
    description: str

    dimensions:int


@app.post('/postModel',tags=["Models"])
async def postModel(model:Model):
    q2 = '''MATCH(C: Models)CREATE (C) -[:hasModel]->(s:Model{name:$name,description:$description,dimensions:$dimensions})'''
    x={"name":model.name,"description":model.description,"dimensions":model.dimensions}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("Model added Successfully")

class Dimension(BaseModel):
    name: str
    desc: str
    weight:float
    CutOff:float
    Rating: list



@app.post('/postDimension',tags=["Dimension"])
async def postDimension(name:str,dim:Dimension):
    q2 = '''match(m:Model{name:$name}) create (m)-[:hasDimension]->(d:Dimension{name:$dimName,description:$description,weight:$weight,cutOff:$cutOff,Rating:$rating})'''
    x={"name":name,"description":dim.desc,"weight":dim.weight,"cutOff":dim.CutOff,"rating":dim.Rating,"dimName":dim.name}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("Dimension added Successfully")


@app.get('/getDimensions' ,tags=["Dimensions"])
async def getDimenisons(name:str):
    q2 = '''match(m:Model{name:$name}) -[:hasDimension]-> (d:Dimension) return collect(d) as Dim
 '''
    x = {"name":name}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)

@app.get('/getDimensionsCount' ,tags=["Dimensions"])
async def getDimenisonsCount(name:str):
    q2 = '''match(m: Models)-[: hasModel]->(k:Model{name:$name})
    match(k) - [: hasDimension]->(x)
    return count(x) as count
 '''
    x = {"name":name}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)

@app.get('/getMax' ,tags=["Dimensions"])
async def Max():
    q2 = '''match (k:SurveyedModel)  return distinct(k) , count(*) as c
 '''
    result = session.run(q2)
    data = result.data()

    json_data = jsonable_encoder(data)
    print(json_data)
    max = -1
    model =""
    for i in json_data:
        if max<i['c']:
            max = i['c']
            model = i['k']['name']
    return (max,model)

class Survey(BaseModel):
    name:str;
    value:int



@app.get('/getResults' ,tags=["Survey"])
async def getResults(orgName:str,sname:str):
    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 '''
    x = {"orgName":orgName,"sname":sname}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)

@app.get('/getarry' ,tags=["Survey"])
async def getList(orgName:str,sname:str):
    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) RETURN collect (v.value) as value
 '''
    x = {"orgName":orgName,"sname":sname}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)

    return (json_data)


@app.post('/postSurveyedResult',tags=["Survey"])
async def postSurveyedResult(orgName: str, sname: str):
    q1 = """match (C: Organisation{name:$name}) create (C)-[:hadSurvey]-> (m:SurveyedModel{name:$modelName})"""
    y = {"modelName": sname, "name": orgName}
    session.run(q1, y)
    return  "Success"

@app.post('/postResults',tags=["Survey"])
async def postResults(survey:Survey,orgname,modelName):
    q2 = '''MATCH(C: Organisation{name:$name}) -[:hadSurvey]->(m:SurveyedModel{name:$modelName}) create (m)-[:hasValue]->(r:Value{name:$vname,value:$value})'''
    x={"name":orgname,"modelName":modelName,"vname":survey.name,"value":survey.value}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("SurveyResults added Successfully")

session.close()
graphdb.close()

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=5000)
