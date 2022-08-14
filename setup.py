import services.metrics_storage as ms
import services.crypto_service as cs
import common.entities.metric

storage = ms.MetricsStorage()
cryptoService = cs.CryptoService()

print("Creating database...")

storage.create_database()

print("Database created.")

metrics = ["KRAKEN:BTCUSD", "KRAKEN:ETHUSD", "KRAKEN:XRPUSD"]

print("Loading historical data...")

for metric in metrics:
    print("Getting real time metrics for {}...".format(metric))

    candles = cryptoService.get_historical_metrics(metric)

    print("Adding historical data for {}".format(metric))

    for candle in candles.of_1m:
        # From the documentation of the cryptowatch API: https://docs.cryptowat.ch/rest-api/markets/ohlc the fields in the "of_1m" array are:
        #[
        #    CloseTime,
        #    OpenPrice,
        #    HighPrice,
        #    LowPrice,
        #    ClosePrice,
        #    Volume,
        #    QuoteVolume
        #]
        
        # Price change = Close - Open
        price_change_absolute = candle[4] - candle[1]
        price_change_percentage = (price_change_absolute) / candle[1] * 100
        newMetric = common.entities.metric.Metric(metric, candle[0]*1000, candle[4], candle[5], price_change_percentage, price_change_absolute)

        # Probably there is a more efficient way of bulk inserting but I did not want to spend time researching on this
        storage.put_metrics(newMetric)
        
    print("Added historical data for {}".format(metric))

print("Historical data loaded.")

print("Testing assessment functions...")

print("Retrieving available metrics...")

metric_names = storage.get_available_metrics()

print("Available metrics: {}".format(metric_names))

print("Retrieving 24 hours historical price data for KRAKEN:BTCUSD...")

historical_data = storage.get_historical_data('KRAKEN:BTCUSD', 'price')

print("Historical data: {}".format(historical_data))

print("Retrieving price metric rank...")

metrics_rank = storage.get_metrics_rank('price')

print("Metrics rank: {}".format(metrics_rank))