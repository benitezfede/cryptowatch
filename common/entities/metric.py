class Metric():
    def __init__(self, name, timestamp, price, volume, change_percent, change_absolute):
        self.name = name
        self.timestamp = timestamp
        self.price = price
        self.volume = volume
        self.change_percent = change_percent
        self.change_absolute = change_absolute

    def __str__(self):
        return '{} price: {} volume: {} @ {}'.format(self.name, self.price, self.volume, self.timestamp)

    def __repr__(self):
        return 'Metric(name={} price={} timestamp={})'.format(self.name, self.price, self.timestamp)

    def __eq__(self, other):
        return self.name == other.name and self.timestamp == other.timestamp and self.price == other.price and self.volume == other.volume and self.change_percent == other.change_percent and self.change_absolute == other.change_absolute
    
    def name(self):
        return self.name
    
    def timestamp(self):
        return self.timestamp
    
    def price(self):
        return self.price
    
    def volume(self):
        return self.volume
    
    def change_percent(self):
        return self.change_percent
    
    def change_absolute(self):
        return self.change_absolute