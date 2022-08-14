import json
import logging
import services.metrics_storage as ms

logger = logging.getLogger()
logger.setLevel(logging.INFO)

storageService = ms.MetricsStorage()

def lambda_handler(event, context):
    result = storageService.get_available_metrics()
    
    response = {}
    response['statusCode'] = 200
    response['body'] = json.dumps(result)
    response['isBase64Encoded'] = False
    
    return response