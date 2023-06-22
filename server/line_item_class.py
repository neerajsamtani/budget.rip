import json


class LineItem:
    def __init__(
        self, id, date, responsible_party, payment_method, description, amount
    ):
        self.id = id
        self.date = date
        self.responsible_party = responsible_party
        self.payment_method = payment_method
        self.description = description
        self.amount = amount

    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "responsible_party": self.responsible_party,
            "payment_method": self.payment_method,
            "description": self.description,
            "amount": self.amount,
        }

    def __repr__(self) -> str:
        return f"""{{
        id: {self.id}
        date: {self.date}
        responsible_party: {self.responsible_party}
        payment_method: {self.payment_method}
        description: {self.description}
        amount: {self.amount}
        }}
        """

    def to_json(self):
        """
        convert the instance of this class to json
        """
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)
