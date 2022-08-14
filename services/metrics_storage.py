import boto3
import configuration.environment as env
import math
from botocore.config import Config

class MetricsStorage():   
    
    def __init__(self):
        self.region = env.AWS_REGION
        self._session = boto3.Session()

        # Recommended Timestream write client SDK configuration:
        #  - Set SDK retry count to 10.
        #  - Use SDK DEFAULT_BACKOFF_STRATEGY
        #  - Set RequestTimeout to 20 seconds .
        #  - Set max connections to 5000 or higher.
        self._write_client = self._session.client('timestream-write', config=Config(read_timeout=20, max_pool_connections=5000,
                                                                        retries={'max_attempts': 10}))
        self._query_client = self._session.client('timestream-query')
        self.paginator = self._query_client.get_paginator('query')
                
    def create_database(self):
        try:
            self.db_arn = self._write_client.create_database(DatabaseName=env.TIME_SERIES_DATABASE_NAME)
            print("Database [%s] created successfully." % env.TIME_SERIES_DATABASE_NAME)
        except self._write_client.exceptions.ConflictException:
            print("Database [%s] exists. Skipping database creation" % env.TIME_SERIES_DATABASE_NAME)
        except Exception as err:
            print("Create database failed:", err)
        
        try:    
            self.tbl_arn = self._write_client.create_table(
                DatabaseName=env.TIME_SERIES_DATABASE_NAME,
                TableName=env.TIME_SERIES_TABLE_NAME,
                RetentionProperties={
                    "MemoryStoreRetentionPeriodInHours": 24,
                    "MagneticStoreRetentionPeriodInDays": 365,
                },
            )
            print("Table [%s] successfully created." % env.TIME_SERIES_TABLE_NAME)
        except self._write_client.exceptions.ConflictException:
            print("Table [%s] exists on database [%s]. Skipping table creation" % (
                env.TIME_SERIES_TABLE_NAME, env.TIME_SERIES_DATABASE_NAME))
        except Exception as err:
            print("Create table failed:", err)


    def put_metrics(self, metric):
        metric_name = metric.name
        metric_timestamp = math.floor(metric.timestamp)
        
        dimensions = [
            {'Name': 'metric', 'Value': metric_name},
        ]

        common_attributes = {
            'Dimensions': dimensions,
            'MeasureValueType': 'DOUBLE',
            'Time': str(metric_timestamp),
            'TimeUnit': 'MILLISECONDS'
        }

        price = {
            'MeasureName': 'price',
            'MeasureValue': str(metric.price)
        }

        volume = {
            'MeasureName': 'volume',
            'MeasureValue': str(metric.volume)
        }
        
        change_percent = {
            'MeasureName': 'change_percent',
            'MeasureValue': str(metric.change_percent)
        }
        
        change_absolute = {
            'MeasureName': 'change_absolute',
            'MeasureValue': str(metric.change_absolute)
        }

        records = [price, volume, change_percent, change_absolute]
        
        try:
            result = self._write_client.write_records(
                DatabaseName=env.TIME_SERIES_DATABASE_NAME, TableName=env.TIME_SERIES_TABLE_NAME, Records=records, CommonAttributes=common_attributes
            )
            print("WriteRecords Status: [%s]" % result['ResponseMetadata']['HTTPStatusCode'])
            
        except self._write_client.exceptions.RejectedRecordsException as err:
            print("RejectedRecords: ", err)
            
            for rr in err.response["RejectedRecords"]:
                print("Rejected Index " + str(rr["RecordIndex"]) + ": " + rr["Reason"])
            
            print("Other records were written successfully. ")
            
        except Exception as err:
            print("Error:", err)
            
    def get_available_metrics(self):
        # Retrieve the metric names available in the database so the user can choose
        query = f"""
                SELECT DISTINCT metric, measure_name 
                FROM "{env.TIME_SERIES_DATABASE_NAME}"."{env.TIME_SERIES_TABLE_NAME}"
                ORDER BY metric, measure_name
                """
        
        return self._execute_query(query)
    
    def get_historical_data(self, metric_name, measure_name):
        # Retrieve the metric names available in the database so the user can choose
        query = f"""
                SELECT measure_value::double, time 
                FROM "{env.TIME_SERIES_DATABASE_NAME}"."{env.TIME_SERIES_TABLE_NAME}"
                WHERE time > ago(24h)
                AND measure_name = '{measure_name}'
                AND metric = '{metric_name}'
                ORDER BY time
                """
        
        return self._execute_query(query)
    
    def get_metrics_rank(self, measure_name):
        # Retrieve the metric names available in the database so the user can choose
        query = f"""
                SELECT metric, measure_name, stddev(measure_value::double) as deviation
                FROM "cryptowatch-db"."metrics"
                WHERE time > ago(24h)
                AND measure_name = '{measure_name}'
                group by metric, measure_name
                order by deviation desc
                """
        
        return self._execute_query(query)
    
    def _execute_query(self, query):
        result = []
        try:
            page_iterator = self.paginator.paginate(QueryString=query)
            
            
            for page in page_iterator:
                result.append(self._parse_query_result(page))
            
        except Exception as err:
            print("Exception while running query:", err)
        
        return result
            
    
    def _parse_query_result(self, query_result):
        query_status = query_result["QueryStatus"]

        progress_percentage = query_status["ProgressPercentage"]
        print(f"Query progress so far: {progress_percentage}%")

        bytes_scanned = float(query_status["CumulativeBytesScanned"]) / env.ONE_GB_IN_BYTES
        print(f"Data scanned so far: {bytes_scanned} GB")

        bytes_metered = float(query_status["CumulativeBytesMetered"]) / env.ONE_GB_IN_BYTES
        print(f"Data metered so far: {bytes_metered} GB")

        column_info = query_result['ColumnInfo']

        print("Metadata: %s" % column_info)
        
        return query_result['Rows']
        

        
    