"""Sample file with Feature Envy violation."""

class Address:
    def __init__(self):
        self.street = ""
        self.city = ""
        self.zip_code = ""

class Customer:
    def __init__(self):
        self.name = ""
        self.address = Address()

    def get_address_info(self):
        return f"{self.address.street}, {self.address.city}, {self.address.zip_code}"
