import pandas
import requests, json

def addPrediction(df):
    #read config file
    configDict = readConfigFile()
    
    #try to use auth and if doesn't work login
    auth, baseUrl = login(configDict)
    authBearer = f'Bearer {auth}'

    #setup result for later, hardcoded output columns here
    result = pandas.DataFrame(columns=[configDict['dataConfig']['idColumn'], 'Explanation/Prescription Flag', 'Explanation/Prescription', 'Explanation/Prescription Amount', "Prediction"])

    #get dataset cols needed for prediction
    df_ColsForPred = df[list(configDict['dataConfig']['columnMap'].keys())]
    apiColValues = [configDict['dataConfig']['columnMap'][x] for x in configDict['dataConfig']['columnMap'].keys()]

    #data cleansing, here making sure bools are represented in the same way as ED Story  
    df_ColsForPred = convertBoolsToStrings(df_ColsForPred)

    #convert DF (along with ID columns seperately) to list for API Calls
    list_fromDf = df_ColsForPred.values.tolist()#[0:100] #limit to 100
    idList = df[configDict['dataConfig']['idColumn']].tolist()

    #page lists as API only accepts 200 records at a time
    pagedDF = [list_fromDf[i:i+200] for i in range(0, len(list_fromDf), 200)]
    pagedId = [idList[i:i+200] for i in range(0, len(idList), 200)]

    #paged API call process
    pageNum = 0
    for pageDF, pageId in zip(pagedDF, pagedId):
        response = predictFromData(pageDF, baseUrl, authBearer, configDict['predictionId'], apiColValues)
        currentOutput = processPredictionResponse(configDict['dataConfig']['idColumn'], pageId, response.json())
        result = result.append(currentOutput)

        pageNum += 1
        print(pageNum)

    print(len(result))

    return result

def processPredictionResponse(idField, sentDf, responseDict):
    #map out response of api to list
    listOfExpPresc = []
    for x in range(len(responseDict['predictions'])):
        eachPred = responseDict['predictions'][x]
        idDefined = sentDf[x]

        if eachPred['prediction'].get('importWarnings') != None:
            print(eachPred['prediction']['importWarnings'])

        if eachPred['status'] == "Success":
            prediction = eachPred['prediction']['total']
            for pred in eachPred['prediction']['middleValues']:
                dictToAdd = {idField : idDefined}
                dictToAdd['Prediction'] = prediction
                if len(pred['columns']) == 2:
                    expl = f'{pred["columns"][0]["columnName"]} is {pred["columns"][0]["columnValue"]} and {pred["columns"][1]["columnName"]} is {pred["columns"][1]["columnValue"]}'
                else:
                    expl = f'{pred["columns"][0]["columnName"]} is {pred["columns"][0]["columnValue"]}'

                dictToAdd['Explanation/Prescription Amount'] = pred['value']
                dictToAdd["Explanation/Prescription"] = expl
                dictToAdd["Explanation/Prescription Flag"] = "Explanation"

                listOfExpPresc.append(dictToAdd)

            for presc in eachPred['prescriptions']:
                dictToAdd = {idField : idDefined}
                dictToAdd['Prediction'] = prediction
                expl = f'change {presc["columns"][0]["columnName"]} to {presc["columns"][0]["columnValue"]}'

                dictToAdd['Explanation/Prescription Amount'] = presc['value']
                dictToAdd["Explanation/Prescription"] = expl
                dictToAdd["Explanation/Prescription Flag"] = "Prescription"

                listOfExpPresc.append(dictToAdd)

    return pandas.DataFrame(listOfExpPresc)


def convertBoolsToStrings(df_input):
    #cleaning of data specific to current use case
    booleandf = df_input.select_dtypes(include=[bool])
    booleanDict = {True : 'True', False : "False"}

    for column in booleandf:
        df_input[column] = df_input[column].map(booleanDict)

    return df_input


def get_output_schema():
    #schema definition required by tabpy and prep builder
    return pd.DataFrame({
        'ID' : prep_string(),
        'Prediction': prep_decimal(),
        'Explanation/Prescription Flag': prep_string(),
        'Explanation/Prescription': prep_string(),
        'Explanation/Prescription Amount': prep_decimal()
    })


def predictFromData(data, baseUrl, auth, predictionId, apiColNames):
    #actaully call the API
    #prepare request
    url = f'{baseUrl}/services/data/v48.0/smartdatadiscovery/predict'
    payloadJson = {"predictionDefinition": predictionId, "type": "RawData", "columnNames": apiColNames, "rows": data}
    headers = {
    'Authorization': auth,
    'Content-Type': 'application/json'
    }
    payload = json.dumps(payloadJson)

    #send request
    response = requests.request("POST", url, headers=headers, data = payload)

    return response


def readConfigFile():
    #read config file with name "predictionConfig.json" in current directory
    with open('predictionConfig.json', 'r') as filein:
        fileString = filein.read()
        fileDict = json.loads(fileString)

        return fileDict

def writeConfigFile(configDict):
    #write to config file (mainly for saving auth details)
    with open('predictionConfig.json', 'w') as fileout:
        json.dump(configDict, fileout)


def login(configDict):
    #test connection first
    payload = {}
    header = {'Authorization': configDict['savedSession']['auth']}
    testUrl = f'{configDict["savedSession"]["url"]}/services/data/v48.0/smartdatadiscovery/predictionDefinitions'

    response = requests.request("GET", testUrl, headers=header, data=payload)
    if response.status_code == 200:
        return configDict['savedSession']['auth'], configDict["savedSession"]["url"]

    #get auth token and instance url
    url = f'{configDict["login"]["url"]}/services/oauth2/token'

    payload = {"grant_type":"password", "client_id": configDict["appCreds"]["clientId"], "client_secret": configDict['appCreds']["clientSecret"],
     "username": configDict['login']['username'], "password":configDict['login']['password']}
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request("POST", url, headers=headers, data = payload)
    respDict = response.json()

    configDict['savedSession']['auth'] = respDict['access_token']
    configDict['savedSession']['url'] = respDict['instance_url']

    writeConfigFile(configDict)

    return respDict['access_token'], respDict['instance_url']
