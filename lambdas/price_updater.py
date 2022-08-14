import logging
import time

import services.metrics_storage as ms
import services.crypto_service as cs
import common.entities.metric

logger = logging.getLogger()
logger.setLevel(logging.INFO)

storageService = ms.MetricsStorage()
cryptoService = cs.CryptoService()

def lambda_handler(event, context):
    metric_names = event.get('metric_names')
    
    print("Metrics requested: {}".format(metric_names))
    
    for metric_name in metric_names:    
        print("Metric name: {}".format(metric_name))
        
        result = cryptoService.get_realtime_metrics(metric_name)

        # Unfortunately the cryptowatch market.get API does not return the timestamp for the "last" price
        timestamp = int(round(time.time() * 1000))

        metric = common.entities.metric.Metric(metric_name, timestamp, result.market.price.last, result.market.volume, result.market.price.change, result.market.price.change_absolute)

        storageService.put_metrics(metric)
        
        print(metric)