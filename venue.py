from helper import slugify
class Venue:
    def __init__(self, name, capacity,address):
        self.name = name
        self.capacity = capacity
        self.address = address
        self.slug = slugify(name)
    def __str__(self):
        return f"{self.name}: {self.capacity} seats  ({self.address})"

 