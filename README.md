****
# Inventory Management System
This is a serverless inventory management system created with AWS services. You can access the system [here](https://d2ngzfpqeh77qd.cloudfront.net/.)

## Environment setup

### Requirements
You need these on your computer before you can proceed with the setup.
* pip 
* git 
* Python >= 3.8 
* aws-cdk

### To Run locally
1. Clone this repository
```
$ git clone https://github.com/SarahTeoh/inventory-management-system.git 
```

2. Ensure CDK is installed
```
$ npm install -g aws-cdk
```

3. Create a python virtual environment:

```
$ python3 -m venv .venv
```

4. Activate the virtual environmetn
On MacOS or Linux
```
$ source .venv/bin/activate
```

On Windows

```
% .venv\Scripts\activate.bat
```

5. Install required dependencies
```
$ pip install -r requirements.txt
```

6. Synthesize (cdk synth) or deploy (cdk deploy) the template
```
$ cdk synth
$ cdk deploy
```

### To Test locally
```
$ python3 -m pytest 
```

### API endpoints
Base path: https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com 
|                                                                                                                                 | Http Method | Integrated Lambda                  | Function                                                                                                                                                                          | Example Parameters                                                                                                                                                                                                                                                                   |
|---------------------------------------------------------------------------------------------------------------------------------|-------------|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [ /inventory ]( https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventory )                                         | POST        | upsertInventoryFunction            | Upsert item. If item with same name and same category doesn't exist, new item is created. If an item with same name and category exists, the item will be updated with new price. | <pre lang="json">{<br> &nbsp;"name": "Thing",<br> &nbsp;"category": "Stationary",<br> &nbsp;"price": 7.6 <br>}</pre>                                                                                                                                                                                                        |
| [ /inventories/filterByDateRange ]( https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventories/filterByDateRange ) | GET         | filterInventoryByDateRangeFunction | Filter items that have `last_updated_dt` within the date range and return total price of the items.                                                                               | <pre lang="json">{<br> &nbsp;"dt_from": "2022-01-01 10:00:00",<br> &nbsp;"dt_to": "2022-01-25 10:00:00" <br>}</pre>                                                                                                                   |
| [ /inventories/aggregate ]( https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventories/aggregate )                 | GET         | aggregateInventoryFunction         | Filter items by category and total price. If `all` is passed, it will return all category.                                                                                        |  <pre lang="json">{<br> &nbsp;"category": "all" <br>}</pre>                                                                                                                                                                                 |
| [ /inventories ]( https://fs2hjjfa0d.execute-api.ap-southeast-1.amazonaws.com/inventories )                                     | POST        | queryInventoryFunction             | Query items with filters, pagination and sorting options.                                                                                                                         | <pre lang="json">{<br> &nbsp;"filters":<br> &nbsp; &nbsp;{<br> &nbsp; &nbsp; &nbsp;"name": "note",<br> &nbsp; &nbsp; &nbsp;"category": "Stationary",<br> &nbsp; &nbsp; &nbsp;"price_range": [1,10]<br> &nbsp; &nbsp;},<br> &nbsp; "pagination":<br> &nbsp; &nbsp;{<br> &nbsp; &nbsp; &nbsp;"page": 1,<br> &nbsp; &nbsp; &nbsp;"limit": 10 <br> &nbsp; &nbsp;}, &nbsp; &nbsp; &nbsp; <br> &nbsp; "sort":<br> &nbsp; &nbsp;{<br> &nbsp; &nbsp; &nbsp;"field": "price",<br> &nbsp; &nbsp; &nbsp;"order": "asc" <br> &nbsp; &nbsp;}<br>}</pre>             |

[<img src="https://run.pstmn.io/button.svg" alt="Run In Postman" style="width: 128px; height: 32px;">](https://app.getpostman.com/run-collection/9636334-96c9786e-d1ba-4984-aa57-e950c20680b9?action=collection%2Ffork&source=rip_markdown&collection-url=entityId%3D9636334-96c9786e-d1ba-4984-aa57-e950c20680b9%26entityType%3Dcollection%26workspaceId%3Ded06f64f-fc04-427f-977f-4f3abacdbff7)


## Architecture
the cloud infrastructure resources are defined and provisioned using AWS Cloud Development Kit (CDK). This is the architecture used.
![Architecture diagram](docs/architecture.drawio.png "Architecture")
AWS Services used and their functions are listed below.
| Amazon Service | Function                                                                                 |
|----------------|------------------------------------------------------------------------------------------|
| API Gateway    | Receive requests and return response                                                     |
| S3             | Host frontend created with React                                                         |
| CloudFront     | Fast content delivery network, acts as distributed cache of frontend hosted in S3 bucket |
| Lambda         | Process requests                                                                         |
| DynamoDB       | Store data                                                                               |

## Data model
The DynamoDB data model looks like this. The detailed diagram can be accessed under [`docs` directory here](docs).
|                         | Type                   | Partition Key | Sort Key        |
|-------------------------|------------------------|---------------|-----------------|
| Inventory Table         | Base Table             | name          | category        |
| CategoryPriceIndex      | Global Secondary Index | category      | price           |
| ItemsLastUpdatedDtIndex | Global Secondary Index | static_pk     | last_updated_dt |
| ItemsPriceIndex         | Global Secondary Index | static_pk     | price           |


Please note that the static_pk value is a constant "PRODUCT". This is because DynamoDB is schemaless,
so in order to retrieve a record we need to provide the partition key(exact match).
We will have to scan the dynamodb table if we don't have a partition key.
This might consume a big amount of Read Capacity Unit(RCU).
So I made up a constant value here as partition key to save cost. 
This is to save cost, but if the amount of data is big, we shall plan to use other design methods like partition sharding instead. 