import numpy as np

# ------------------------------------------------------------
# WATER FORMULA
# ------------------------------------------------------------
def predict_water(humidity, greenery):
    """
    Bereken hoeveelheid water (ml) gebaseerd op bodemvocht en groenpercentage
    """
    return 261.83 - humidity * 3.13314695 + greenery * 2.13997997

# ------------------------------------------------------------
# VALVE TIME CALCULATION
# ------------------------------------------------------------
def valve_open_time_ml(V_ml):
    """
    Bereken hoe lang de solenoïde klep open moet staan voor een doelvolume V_ml.
    Retourneert tijd in seconden. Geeft None terug als V_ml buiten bereik ligt.
    """
    a = 0.11455309
    b = 36.75567689
    c = 19.817595 - V_ml

    discriminant = b**2 - 4*a*c
    if discriminant < 0:
        return None

    t = (-b + np.sqrt(discriminant)) / (2*a)
    return t

# ------------------------------------------------------------
# VOORBEELD: input waarden
# ------------------------------------------------------------
humidity = 30.52
greenery = 15.21

# Bereken water en klep open tijd
water_ml = predict_water(humidity, greenery)
valve_time_s = valve_open_time_ml(water_ml)

print(f"Input - Humidity: {humidity}%, Greenery: {greenery}%")
print(f"Predicted water: {water_ml:.2f} ml")
if valve_time_s is not None:
    print(f"Valve should open for: {valve_time_s:.2f} seconds")
else:
    print("Predicted water is out of the calibrated range!")
