# TabpyBulkScoring
![BetterTogether](https://user-images.githubusercontent.com/39613850/117524151-46877f00-aff7-11eb-891f-fbb021546ae3.gif)



## Dependency
Tabpy : All the packages needed in the virtualenv is in requirements.txt
Tableau : Tableau Desktop and Tableau Prep Builder
Salesforce : Prediction or Sandbox includer Einstein Analytics Plus Licence

## Python Script and Tanpy Setup
### Python Packages Installation
1) Install Pip (https://pip.pypa.io/en/stable/installing/)
2) Install Virtualenv (https://virtualenv.pypa.io/en/latest/installation.html)

* typically the command here should be this in your terminal:

    * pip install virtualenv

3) Go to where you downloaded the script, requirements.txt, and predictionConfig.json file in your terminal and type:

* virtualenv env
* *this creates a virtual environment as to not mess with your system level Python installation*

4) Now that the virtual environment has been created, type this to enable it:

* source env/bin/activate

5) Install all the packages needed in the virtualenv using this command:

* pip install -r requirements.txt

These are the instructions to get your Python environment setup to run the script. Once you’ve done this once, you can always go back to this directory and just do steps 4 and 5 to re-run the script, no need on running through the installation steps again. *Note that this all requires the use of Python 3, not Python 2.7.*

### Prediction Configration JSON Setup

```predictionConfig.json
{
    "predictionId": "<Einstein Discovery Model ID>",
    "dataConfig": {
        "idColumn": "ID",
        "columnMap": {
            "MarketingCampagn__c": "<API name>",
            "YearOfServices__c": "<API name>",
            "Product__c": "<API name>",
            "Department__c": "<API name>",
            "Prefecture__c": "<API name>"
        }
    },
    "savedSession": {
        "auth": "<your org token>",
        "url": "<your org domain>"
    },
    "appCreds": {
        "clientId": "<clientID>",
        "clientSecret": "<clinetSecret>"
    },
    "login": {
        "username": "<your org username>",
        "password": "<your org password>",
        "url": "https://login.salesforce.com"
    }
}

```


* *predictionId →* the ID of your deployed model from Einstein Discovery, found in the Model Manager in EA
* *dataConfig →* the definition of your prediction file structure and how it relates back to your model
    * *idColumn →* an ID column is needed in your prediction dataset, this is to allow us to later map the explanations/prescriptions back to the original dataset as they are of different granularities
    * *columnMap →* the structure of this key value pair is *“<column name in predictions dataset>”:“<column name in your Einstein Discovery model (API name)>”*


* *savedSession →* if you already have an auth token or know how to get it, you can paste it in here along with your instance url. *Note: if you don’t know how to get the auth token, not to worry, just leave this part as is. you can use the login node below instead.*
* *appCreds →* these are your clientId and clientSecret keys which are found when you created your Connected App within a Salesforce instance
* *login →* instead of filling in the “savedSession” node, you can put in your username and password here. The url will either be “https://login.salesforce.com” (https://login.salesforce.xn--com-9o0a/) for production or “https://test.salesforce.com” (https://test.salesforce.xn--com-9o0a/) for sandbox. 

## Running Tabpy
Running Tabpy

Now that you’ve setup Python and the prediction configuration file, you can run the Tabpy server. While being in the same directory in your terminal with the virtualenv activated, type:

tabpy --conf="tabpy.conf"

*Note:* The tabpy.conf file should be in the same directory as everything else since it is included in the Google Drive repository. This configuration file has all the default settings except for extending the timeout time to 300 seconds. This is because to score 20k records, it can take longer than the 30 second default timeout time. 

## Prep Builder Setup
Lastly, the Prep Builder flow has to be setup to use the Python script for bulk scoring. The HRPrediction.tflx file in the Google Drive has this flow already setup from our HR demo. To setup a new flow:

1) Use “Connect to Data” and select data source (“Text file” for CSV)
2) Using “+” (plus sign) on the connection, add “Script” step. Within the script step this should be the setup:

* *Connection type →* Tableau Python (Tabpy) Server
* *Connect to Tableau Python (Tabpy) Server*
    * *Server:* localhost
    * *Port:* 9004
* *File Name →* EDPrediction.py (or whatever you named the file that you downloaded from the repo)
* *Function Name →* addPrediction (unless this name was changed by you)

3) Create an output step from the script step. I have saved the file in a hyper extract but it can be exported out based on all the supported formats within Prep Builder.

*(Optional Extra Steps to include the predictions on the original file)*

4) Add a second branch to the output of the script step with an aggregate step. Group by the Id field and aggregate the Prediction field with the function "AVG"
6) Add a join step after the aggregation, with the left side of the join being the original file, and the right side being the output of the aggregated step. Set the join to be an outer left join.
7) Create an output step coming from this join step to create a file which has all the original information along with a new prediction column
