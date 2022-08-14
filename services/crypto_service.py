import cryptowatch as cw
import logging
import configuration.environment as env

class CryptoService():
    
    def __init__(self):
        cw.api_key = env.CRYPTOWATCH_API_KEY
        logging.basicConfig()
        # Get the cryptowatch logger and set it to DEBUG
        logging.getLogger("cryptowatch").setLevel(logging.DEBUG)
        
    def get_realtime_metrics(self, market_name):
        try:
            return cw.markets.get(market_name)
        except Exception as err:
            print("Error:", err)
            
    def get_historical_metrics(self, market_name):
        try:
            return cw.markets.get(market_name, ohlc=True, periods=["1m"])
        except Exception as err:
            print("Error:", err)
        