class Shift:
    def __init__(self, name, length, restricted_shifts):
        self.name = name
        self.length = length
        self.restricted_shifts = restricted_shifts
    
    def __str__(self):
        return f"Shift(name={self.name}, length={self.length}, restricted_shifts={self.restricted_shifts}) \n"
