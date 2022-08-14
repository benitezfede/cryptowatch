import json
import logging
import services.metrics_storage as ms

logger = logging.getLogger()
logger.setLevel(logging.INFO)

storageService = ms.MetricsStorage()

def lambda_handler(event, context):
    print("Event: {}".format(event))
    
    querystring = event.get('queryStringParameters')
    
    print("QS: {}".format(querystring))
    
    metric_name = querystring.get('metric_name')
    measure_name = querystring.get('measure_name')
    
    print("Metric name: {}".format(metric_name))
    print("Measure name: {}".format(measure_name))
    
    result = storageService.get_historical_data(metric_name, measure_name)
    
    response = {}
    response['statusCode'] = 200
    response['body'] = json.dumps(result)
    response['isBase64Encoded'] = False
    
    return response