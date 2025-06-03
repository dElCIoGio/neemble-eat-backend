

def parse_opening_hours(form: dict) -> dict:
    """
     return eg: {'monday': '09:00-22:00', 'tuesday': '09:00-22:00', 'wednesday': '09:00-22:00', 'thursday': '09:00-22:00', 'friday': '09:00-22:00', 'saturday': '09:00-22:00', 'sunday': '09:00-22:00'}
    """

    opening_hours = {}
    for key, value in form.items():
        # keys look like 'openingHours[monday]'
        if key.startswith("opening_hours["):
            day = key[len("opening_hours["):-1]
            opening_hours[day] = value
    return opening_hours