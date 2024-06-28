class Nurse:
    def __init__(self, name, max_shifts, max_total_minutes, min_total_minutes, max_consecutive_shifts, min_consecutive_shifts, min_consecutive_days_off, max_weekends):
        self.name = name
        self.max_shifts = max_shifts
        self.max_total_minutes = max_total_minutes
        self.min_total_minutes = min_total_minutes
        self.max_consecutive_shifts = max_consecutive_shifts
        self.min_consecutive_shifts = min_consecutive_shifts
        self.min_consecutive_days_off = min_consecutive_days_off
        self.max_weekends = max_weekends
    
        
    def __str__(self):
        return f"Nurse(name={self.name}, max_shifts={self.max_shifts}, max_minutes={self.max_minutes}, min_minutes={self.min_minutes}, " \
                f"max_consecutive_shifts={self.max_consecutive_shifts}, min_consecutive_shifts={self.min_consecutive_shifts}, " \
                f"min_consecutive_days_off={self.min_consecutive_days_off}, max_weekends={self.max_weekends}, " \
                f"days_off={self.days_off},)"