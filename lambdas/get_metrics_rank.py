import json
import logging
import services.metrics_storage as ms

logger = logging.getLogger()
logger.setLevel(logging.INFO)

storageService = ms.MetricsStorage()

def lambda_handler(event, context):
    querystring = event.get('queryStringParameters')
    
    measure_name = querystring.get('measure_name')
    
    result = storageService.get_metrics_rank(measure_name)
    
    response = {}
    response['statusCode'] = 200
    response['body'] = json.dumps(result)
    response['isBase64Encoded'] = False
    
    return response