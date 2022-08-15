# Disclaimer

I have no experience with Python but I decided to make an effort and use it as it is the language being used in Monte Carlo. So it won't be a surprise if there are things that can be better or simpler using other Python modules.

Please also read the section "Things to improve if there was more time" as I mention there what I could have done to make this application more "complete"

# Architecture

In order to be able to develop this application with a simple and scalable architecture I have chosen to leverage AWS cloud and use the following AWS Services:
+ Timestream database: 
    + It is a managed, serverless database that automatically scales to handle the load. It has built in functions to analyze time series which will help me for the rank query and also it is more efficient than other databases to query data for short periods as it keeps part of the data in memory (in our case 24 hours).
+ Lambdas: Allows us to create serverless functions that are easy to modify and deploy. They are also scalable, so if we need to handle more load more Lambdas will be spinned up to handle it. Our queries run in less than a second so we won't face the Lambda limitation of 15 minutes of execution. I created 4 Lambdas (one for each requested function):
    + Metrics updater: It is a scheduled Lambda that runs every minute to collect the latest metrics from Cryptowatch and store them in the TimeStream database.
    + Get available metrics: Retrieves the metrics that have values in the last 24 hours so the user can choose them and retrieve the historical data
        + The available metrics are: KRAKEN:BTCUSD, KRAKEN:ETHUSD and KRAKEN:XRPUSD
        + The available measures are: price, volume, change_percentage (the % of price changed), change_absolute (the absolute price change)
    + Get historical data: Retrieves the last 24 hours of data for a given metric (ie KRAKEN:BTCUSD) and measure (ie price, volume, change of price)
    + Get metrics rank: Retrieves the rank of the metrics based on their standard deviation over the last 24 hours
+ EventBridge: We will use EventBridge rules to schedule the Lambda that will gather the data every minute. We created an EventBridge rule for that triggers the Lambda every minute with a constant JSON input requesting the following metrics: KRAKEN:BTCUSD, KRAKEN:ETHUSD and KRAKEN:XRPUSD 
+ API Gateway: It will allow us to expose our REST API to the public and internally consuming the Lambda functions we created. Maps the HTTP requests to a Lambda invokation passing the parameters in the querystring inside the event of the Lambda. 

Regarding some implementation decisions, I decided to abstract the persistence and the crypto library into 2 services, so if we change the crypto provider or decide to store the data in a different database / file / etc we just need to change those service classes:
+ ./services/crypto_service.py
+ ./services/metrics_storage.py

# Deployed APIs

As most of the AWS setup was done manually, I left deployed the APIs in my account so they can be tested any time. I can walk anyone through how to create each of the services used in the 30 minutes call we will have to discuss the solution.

These are the URLs for the APIs:
1) Get available metrics: https://18pdsdqxi7.execute-api.us-east-1.amazonaws.com/pricetracker/metrics
2) Get historical data: https://18pdsdqxi7.execute-api.us-east-1.amazonaws.com/pricetracker/historicalprices?metric_name=KRAKEN:BTCUSD&measure_name=price (Note the timezone for the time is UTC, if you want to see the last value inserted you need to scroll down to the bottom)
3) Get metrics rank: https://18pdsdqxi7.execute-api.us-east-1.amazonaws.com/pricetracker/metricsrank?measure_name=price

The price updater one it is not public but it is being executed every minute and can be checked with the historical prices API or in the following picture it can be seen how it has been executing in the last 3 hours. NOTE: it is only requesting metrics for: KRAKEN:BTCUSD, KRAKEN:ETHUSD and KRAKEN:XRPUSD

![image](https://user-images.githubusercontent.com/4431460/184548318-f3775dfc-2ad4-4150-93ce-c8c01b778160.png)


# Things to improve if there was more time:

+ Unit tests should be added to the project
+ Dependency Injection and programming with interfaces (given my lack of Python knowledge I am not sure if there is any framework for this)
+ Make the bulk loading more efficient by loading from a CSV or similar
+ The metrics rank is returning the ordered rank from the database but the rank number is missing (1/3, 2/3, 3/3)
+ Parsing the results of the queries, now it is just returning what it gets from the database
+ Create a lambda layer with the shared classes between all the lambdas
+ Create Infrastructure as Code to handle lambda deployments and updates, create the EventBridge scheduler and the APIs in API Gateway
+ Raising alerts using Cloudwatch when a price is not inserted in a minute or a given time period
+ Input parameter validation in the Lambdas
+ The input metrics for the scheduled lambda are now hardcoded in the EventBridge Rule parameters, we might want to pick up those from a database

# Answering Questions

## Scalability: 

### what would you change if you needed to track many metrics? 

I would create scheduled job per metric, this will trigger a lambda invokation per metric, instead of how it is implemented today that a single lambda is querying for all the metrics and inserting them in the database. Also if needed the concurrency of the Lambda might need to be increased.

### What if you needed to sample them more frequently? 

We can use AWS Kinesis to ingest the data instead of a scheduled Lambda, I saw as well that AWS has some services for IoT to ingest data, that then it is sent to Kinesis as well but I would need to do more research on that to understand if it is needed and also have more concrete numbers on how frequent the data should be sampled. The downside of this is that we will need to create our own service and manage it (monitor it, scale it up and down when needed, implement how to bring it back if it crashes, etc). Also in that service we could use the Cryptowatch Websockets instead of polling for the data.

We cannot sample faster with scheduled lambdas because the minimum ammount is 1 minute for the scheduled rule.

### what if you had many users accessing your dashboard to view metrics?

API Gateway should scale up automatically, lambda and timestream also so the application should be fine with a large number of users. The data queried is not static so that is why I am not considering a cache as an option. Potentially other improvements could be to use Lambda @ Edge to have the Lambdas running on locations closer to the user.

## Testing: how would you extend testing for an application of this kind (beyond what you implemented)?

I would add the following tests:
+ Check that the metrics are inserted every minute, if not create a CW alarm or similar.
+ Query the APIs and make sure they are returning the correct number of results (ie each metric and measure should return 1440 values for the historical API), if not there is data missing
+ Add Unit tests and also Integration Tests for the 4 APIs
+ Load tests to see if we face any unexpected limitation (sometimes we reach AWS limits that we were not aware of)

## Feature request: to help the user identify opportunities in real-time, the app will send an alert whenever a metric exceeds 3x the value of its average in the last 1 hour. For example, if the volume of GOLD/BTC averaged 100 in the last hour, the app would send an alert in case a new volume data point exceeds 300. Please write a short proposal on how you would implement this feature request.

I would run a query to the database that gives me the average measures for the metric we are inserting and check if it is 3x. If it is, I will send a message to an SNS so any application can subscribe to that notification and report it. I think this is OK from the point of view of performance as the Timestream database does this calculations with very low latency.

# Setup

I am assuming that you have your AWS profile configured with full permissions to create resources in the linked AWS Account

All the infrastructure except the database should be created manually. I created a script that will create the ZIP files for the 4 lambdas but the Lambdas creation, EventBridge Scheduler and API Gateway setup must be done manually.

Data Insertion and database creation

To insert the historical data in the setup I am not doing a bulk insert because I did not want to spend time looking on how to do this, I am inserting the values one by one which is not efficient but this part was out of scope of the assessment so I preferred to focus on the other requirements.

Run: `pip install -r requirements.txt`

In setup.py the database is created, the historical data inserted and there are sample invocations to the queries (using the services directly not the Lambdas)
