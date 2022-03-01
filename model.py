from fastapi import FastAPI
from typing import Optional, Any, List
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase


import uvicorn as uvicorn
import numpy as np
import pandas as pd



cutoff = {
        "Shop Floor Automation" : 2.5,
"verticalIntegration":2.5,
"horizontalIntegration" :2.5,
"Enterprise Automation" :2.5,
"Facility Automation" :2.5,
"ProductLifeCycle" : 2.5,
"Shop Floor Connectivityn" : 2.5,
"Enterprise Connectivityn" : 2.5,
" Facility Connectivity": 2.5,
"Shop Floor Intelligence" : 2.5,
"Enterprise Intelligence": 2.5,
"Facility Intelligence": 2.5,
"Leadership Competency": 2.5,
"Workforce Learning & Development ": 2.5,
"Strategy & governance": 2.5,
"Inter- & intra-company collaboration": 2.5,
    }
weight = {
        "Shop Floor Automation" :0.111,
"verticalIntegration": 0.111,
"horizontalIntegration" : 0.111,
"Enterprise Automation" : 0.037,
"Facility Automation" :0.037,
"ProductLifeCycle" :0.037,
"Shop Floor Connectivityn" :0.037,
"Enterprise Connectivityn" :0.037,
" Facility Connectivity":0.037,
"Shop Floor Intelligence" :0.037,
"Enterprise Intelligence": 0.037,
"Facility Intelligence": 0.037,
"Leadership Competency": 0.08325,
"Workforce Learning & Development ":0.08325,
"Strategy & governance":0.08325,
"Inter- & intra-company collaboration":0.08325,
    }

class MPI:
    table = {}
    cutoff = 2.5

    def __init__(self, values, CompanyName):
        self.d = values
        self.name = CompanyName
        MPI.table[self.name] = {}
        for i in self.d:
            MPI.table[self.name][i['Dim']] = i['value']

    @staticmethod
    def findDeprivation_matrix():
        dep_matrix = pd.DataFrame(MPI.table)
        for company in dep_matrix.columns:
            for dimension in dep_matrix.index:
                value = dep_matrix[company].loc[dimension]  # provide weight here
                ###Provide cut off
                if (value >= cutoff[dimension]):
                    dep_matrix[company].loc[dimension] = 0
                else:
                    dep_matrix[company].loc[dimension] = 1  # provide weight here
        return dep_matrix

    @staticmethod
    def total_Cj():
        dep_matrix = MPI.findDeprivation_matrix()
        totalCj = pd.DataFrame(dep_matrix.sum(), columns=["Total"])  # Cj Vector
        count = 0
        cut = 6
        print(totalCj)
        for i in totalCj.index:
            if totalCj.loc[i]['Total'] >= cut:  # If company totalCj is greater than cut
                count = count + 1
            else:
                totalCj.loc[i]['Total'] = 0
                for j in dep_matrix.index:
                    dep_matrix.loc[j][i] = 0
        #         print(count)
        HeadCount = count / len(dep_matrix.columns)
        print("HeadCount", HeadCount)
        return totalCj, dep_matrix, HeadCount

    @staticmethod
    def deprivation_share():
        k = MPI.total_Cj()
        total = k[0]
        dep_matrix = k[1]
        share = {}
        for i in total.index:
            value = total.loc[i]['Total'] / len(dep_matrix.index)
            share[i] = value
        print(share)
        return share

    @staticmethod
    def adjusted_headCount():
        k = MPI.total_Cj()
        total_Cj = k[0]
        dep_matrix = k[1]
        HeadCount = k[2]
        total = 0
        count = 0
        #         print(total_Cj)
        for i in total_Cj.index:
            if (total_Cj.loc[i]['Total'] > 0):
                share = total_Cj.loc[i]['Total'] / len(dep_matrix.index)
                #                 print("share" , share)
                total = total + share
                count = count + 1
        #         print(total)
        average = (total / count)
        #         print(average)
        adjusted_headCount = HeadCount * average
        #         print(adjusted_headCount)
        return adjusted_headCount, dep_matrix

    @staticmethod
    def UnCensored_HeadCountRatio():
        k = MPI.adjusted_headCount()
        dep_matrix = k[1]
        #         adjusted_headCount = k[0]
        trans = dep_matrix.transpose()
        print(trans)
        trans = pd.DataFrame(trans.sum(), columns=["Total"])
        print(trans)
        Uh = []
        for i in trans.index:
            Uh.append(trans.loc[i]['Total'] / len(trans.index))
        print(Uh)
        return Uh

    @staticmethod
    def Censored_HeadCountRatio():
        k = MPI.adjusted_headCount()
        dep_matrix = k[1]

        for company in dep_matrix.columns:
            for dimension in dep_matrix.index:
                dep_matrix[company].loc[dimension] = dep_matrix[company].loc[dimension] * weight[dimension]
        print(dep_matrix)
        total = pd.DataFrame(dep_matrix.sum(), columns=["Total"])
        cutoff = 0.5
        for i in total.index:
            if (total.loc[i]['Total'] < cutoff):
                dep_matrix.drop(i, inplace=True, axis=1)
        print(total)
        t = dep_matrix.transpose()  # Companies that has Cj greater than zero
        print(t)
        total2 = pd.DataFrame(t.sum(), columns=["Total"])  # calculating the sum for unfit companies
        #         print(total2)
        Ch = {}

        for i in t.columns:
            count = 0
            for j in t.index:
                if (t.loc[j][i] != 0):
                    count = count + 1
            Ch[i] = (count / len(total2.index))
        return Ch

    @staticmethod
    def M0():
        k = MPI.Censored_HeadCountRatio()
        dep = MPI.findDeprivation_matrix()
        s = 0
        for i in dep.index:
            s = s + k[i] * (weight[i] / len(dep.index))
        new_adjusted_headcount = s
        return new_adjusted_headcount


# MPI(com1,"Com1")
# MPI(com2,"Com2")
# MPI(com3,"Com3")
# MPI(com4,"Com4")




















app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# graphdb = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "yash"), max_connection_lifetime=1)
graphdb = GraphDatabase.driver(uri="neo4j+s://f951f243.databases.neo4j.io", auth=("neo4j", "08_xJvvomlHaYsaUnUfXiM8hFQmvRijMzPDed63f_y0"), max_connection_lifetime=1)
session = graphdb.session()


com1 = [
    {
        "Dim": "Shop Floor Automation",
        "value": 4
    },
    {
        "Dim": "verticalIntegration",
        "value": 0
    },
    {
        "Dim": "horizontalIntegration",
        "value": 5
    },
    {
        "Dim": "Enterprise Automation",
        "value": 4
    },
    {
        "Dim": "Facility Automation",
        "value": 1
    },
    {
        "Dim": "ProductLifeCycle",
        "value": 5
    },
    {
        "Dim": "Shop Floor Connectivityn",
        "value": 0
    },
    {
        "Dim": "Enterprise Connectivityn",
        "value": 1
    },
    {
        "Dim": " Facility Connectivity",
        "value": 1
    },
    {
        "Dim": "Shop Floor Intelligence",
        "value": 1
    },
    {
        "Dim": "Enterprise Intelligence",
        "value": 0
    },
    {
        "Dim": "Facility Intelligence",
        "value": 4
    },
    {
        "Dim": "Leadership Competency",
        "value": 0
    },
    {
        "Dim": "Workforce Learning & Development ",
        "value": 3
    },
    {
        "Dim": "Strategy & governance",
        "value": 1
    },
    {
        "Dim": "Inter- & intra-company collaboration",
        "value": 0
    }
]
com2 = [
    {
        "Dim": "Shop Floor Automation",
        "value": 0
    },
    {
        "Dim": "verticalIntegration",
        "value": 2
    },
    {
        "Dim": "horizontalIntegration",
        "value": 4
    },
    {
        "Dim": "Enterprise Automation",
        "value": 0
    },
    {
        "Dim": "Facility Automation",
        "value": 1
    },
    {
        "Dim": "ProductLifeCycle",
        "value": 0
    },
    {
        "Dim": "Shop Floor Connectivityn",
        "value": 2
    },
    {
        "Dim": "Enterprise Connectivityn",
        "value": 3
    },
    {
        "Dim": " Facility Connectivity",
        "value": 5
    },
    {
        "Dim": "Shop Floor Intelligence",
        "value": 5
    },
    {
        "Dim": "Enterprise Intelligence",
        "value": 0
    },
    {
        "Dim": "Facility Intelligence",
        "value": 2
    },
    {
        "Dim": "Leadership Competency",
        "value": 5
    },
    {
        "Dim": "Workforce Learning & Development ",
        "value": 1
    },
    {
        "Dim": "Strategy & governance",
        "value": 1
    },
    {
        "Dim": "Inter- & intra-company collaboration",
        "value": 4
    }
]
com3 = [
    {
        "Dim": "Shop Floor Automation",
        "value": 3
    },
    {
        "Dim": "verticalIntegration",
        "value": 0
    },
    {
        "Dim": "horizontalIntegration",
        "value": 5
    },
    {
        "Dim": "Enterprise Automation",
        "value": 1
    },
    {
        "Dim": "Facility Automation",
        "value": 1
    },
    {
        "Dim": "ProductLifeCycle",
        "value": 4
    },
    {
        "Dim": "Shop Floor Connectivityn",
        "value": 5
    },
    {
        "Dim": "Enterprise Connectivityn",
        "value": 5
    },
    {
        "Dim": " Facility Connectivity",
        "value": 1
    },
    {
        "Dim": "Shop Floor Intelligence",
        "value": 4
    },
    {
        "Dim": "Enterprise Intelligence",
        "value": 3
    },
    {
        "Dim": "Facility Intelligence",
        "value": 5
    },
    {
        "Dim": "Leadership Competency",
        "value": 4
    },
    {
        "Dim": "Workforce Learning & Development ",
        "value": 0
    },
    {
        "Dim": "Strategy & governance",
        "value": 0
    },
    {
        "Dim": "Inter- & intra-company collaboration",
        "value": 2
    }
]
com4 = [
    {
        "Dim": "Shop Floor Automation",
        "value": 1
    },
    {
        "Dim": "verticalIntegration",
        "value": 1
    },
    {
        "Dim": "horizontalIntegration",
        "value": 5
    },
    {
        "Dim": "Enterprise Automation",
        "value": 1
    },
    {
        "Dim": "Facility Automation",
        "value": 5
    },
    {
        "Dim": "ProductLifeCycle",
        "value": 2
    },
    {
        "Dim": "Shop Floor Connectivityn",
        "value": 0
    },
    {
        "Dim": "Enterprise Connectivityn",
        "value": 0
    },
    {
        "Dim": " Facility Connectivity",
        "value": 4
    },
    {
        "Dim": "Shop Floor Intelligence",
        "value": 0
    },
    {
        "Dim": "Enterprise Intelligence",
        "value": 5
    },
    {
        "Dim": "Facility Intelligence",
        "value": 1
    },
    {
        "Dim": "Leadership Competency",
        "value": 4
    },
    {
        "Dim": "Workforce Learning & Development ",
        "value": 2
    },
    {
        "Dim": "Strategy & governance",
        "value": 4
    },
    {
        "Dim": "Inter- & intra-company collaboration",
        "value": 3
    }
]


@app.get('/insert' ,tags=["DataFrame"])
async def insert():
    # orgName: str, sname: str
 #    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 # '''
 #    x = {"orgName":orgName,"sname":sname}
 #    result = session.run(q2,x)
 #    data = result.data()
 #    json_data = jsonable_encoder(data)

    MPI(com1,"Com1")
    MPI(com2,"Com2")
    MPI(com3,"Com3")
    MPI(com4,"Com4")

    return "Done"


@app.get('/getAdjustedHeadCount' ,tags=["DataFrame"])
async def insert():
    # orgName: str, sname: str
 #    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 # '''
 #    x = {"orgName":orgName,"sname":sname}
 #    result = session.run(q2,x)
 #    data = result.data()
 #    json_data = jsonable_encoder(data)

    k = MPI.adjusted_headCount()
    m = k[0]
    # print(m)
    return m


@app.get('/getUncensoredHeadCount' ,tags=["DataFrame"])
async def Uncensored():
    # orgName: str, sname: str
 #    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 # '''
 #    x = {"orgName":orgName,"sname":sname}
 #    result = session.run(q2,x)
 #    data = result.data()
 #    json_data = jsonable_encoder(data)


    k = MPI.UnCensored_HeadCountRatio()
    # print(k)
    return k


@app.get('/getCensoredHeadCount' ,tags=["DataFrame"])
async def censored():
    # orgName: str, sname: str
 #    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 # '''
 #    x = {"orgName":orgName,"sname":sname}
 #    result = session.run(q2,x)
 #    data = result.data()
 #    json_data = jsonable_encoder(data)
    k = MPI.Censored_HeadCountRatio()
    # print(k)
    return k

@app.post('/addParentNode',tags=["Organisation"])
async def addParentNode():

    q2 = '''CREATE (ParentNode: Survey{name:"Survey"}) '''
    q3 = """ CREATE (m: Models{name:"Models"})"""
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


@app.get('/getCompanies1' ,tags=["Organisation"])
async def getComapnies1():

    q2 = '''MATCH (n:Organisation) RETURN  (n.name) as Organisations ,(n.sector) as Sector  ORDER BY n.name'''
    result = session.run(q2)
    data = result.data()
    json_data = jsonable_encoder(data)
    print(json_data)
    return (json_data)


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
    rank: int



@app.post('/postDimension',tags=["Dimension"])
async def postDimension(name:str,dim:Dimension):
    q2 = '''match(m:Model{name:$name}) create (m)-[:hasDimension]->
    (d:Dimension{name:$dimName,description:$description,weight:$weight,cutOff:$cutOff,Rating:$rating, rank:$rank})'''
    x={"name":name,"description":dim.desc,"weight":dim.weight,"cutOff":dim.CutOff,"rating":dim.Rating,"dimName":dim.name,"rank":dim.rank}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("Dimension added Successfully")


@app.get('/getDimensions' ,tags=["Dimensions"])
async def getDimenisons(name:str):
    q2 = '''match(m:Model{name:$name}) -[:hasDimension]-> (d:Dimension) 
    return d.Rating as Rating, d.name as name, d.rank as rank, d.description as description,
    d.weight as weight, d.cutOff as cutoff
    ORDER BY d.rank
 '''
    # return collect(d) as Dim
    
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
    rank: int


@app.get('/getResults' ,tags=["Survey"])
async def getResults(orgName:str,sname:str):
    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) return v.name as Dim,v.value as value
 '''
    x = {"orgName":orgName,"sname":sname}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return json_data




@app.get('/getarry' ,tags=["Survey"])
async def getList():
 #    q2 = '''match(o:Organisation{name:$orgName})-[:hadSurvey]->(s:SurveyedModel{name:$sname})-[:hasValue]->(v:Value) RETURN collect (v.value) as value
 # '''
 #    x = {"orgName":orgName,"sname":sname}
 #    result = session.run(q2,x)
 #    data = result.data()
 #    json_data = jsonable_encoder(data)

     k = MPI.Censored_HeadCountRatio()
     print(MPI.table)
     return (k)


@app.post('/postSurveyedResult',tags=["Survey"])
async def postSurveyedResult(orgName: str, sname: str):
    q1 = """match (C: Organisation{name:$name}) create (C)-[:hadSurvey]-> (m:SurveyedModel{name:$modelName})"""
    y = {"modelName": sname, "name": orgName}
    session.run(q1, y)
    return  "Success"

@app.post('/postResults',tags=["Survey"])
async def postResults(survey:Survey,orgname,modelName):
    q2 = '''MATCH(C: Organisation{name:$name}) -[:hadSurvey]->(m:SurveyedModel{name:$modelName}) 
    create (m)-[:hasValue]->(r:Value{name:$vname,value:$value, rank: $rank})'''
    x={"name":orgname,"modelName":modelName,"vname":survey.name,"value":survey.value,
       "rank":survey.rank}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return ("SurveyResults added Successfully")

















@app.get('/getCompanies/{model}' ,tags=["A"])
async def getCompanies(model: str):
    q2 = ''' MATCH (S: Survey) -[:hasOrganisation]->(O: Organisation) - [:hadSurvey] -> 
            (SM: SurveyedModel{name:$model})
             RETURN O.name as orgName
             ORDER BY O.name'''
    x = {"model":model}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return json_data

@app.get('/getAnalysisData/{model}' ,tags=["A"])
async def getAnalysisData(model:str):
    q2 = ''' MATCH (S: Survey) -[:hasOrganisation]->(O: Organisation) - [:hadSurvey] -> 
            (SM: SurveyedModel{name:$model}) - [:hasValue] -> (V:Value)
             RETURN O.name as orgName, V.name as name, V.value as value, V.rank as rank
             ORDER BY O.name, V.rank'''
    x = {"model":model}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return json_data

@app.get('/getAnalysisDataForCompany/{model}/{company}' ,tags=["A"])
async def getAnalysisDataForCompany(model:str,company: str):
    q2 = ''' MATCH (S: Survey) -[:hasOrganisation]->(O: Organisation{name:$company}) - [:hadSurvey] -> 
            (SM: SurveyedModel{name:$model}) - [:hasValue] -> (V:Value)
             RETURN O.name as orgName, V.name as name, V.value as value'''
    x = {"model":model, "company": company}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return json_data

@app.get('/getDimensionDetails/{model}' ,tags=["A"])
async def getDimensionDetails(model:str):
    q2 = ''' MATCH (Models: Models) -[:hasModel]->(M:Model{name:$model}) - [:hasDimension] -> 
            (D:Dimension) 
            RETURN D.name as name, D.weight as weight, D.cutOff as cutoff
             '''
    x = {"model":model}
    result = session.run(q2,x)
    data = result.data()
    json_data = jsonable_encoder(data)
    return json_data








session.close()
graphdb.close()

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=5001)
