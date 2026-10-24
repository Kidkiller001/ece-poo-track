class Venue:
    def __init__(self, name, capacity,address):
        self.name = name
        self.capacity = capacity
        self.address = address
        
    def __str__(self):
        return f"{self.name}: {self.capacity} seats  ({self.address})"