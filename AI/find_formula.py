import numpy as np
from scipy.optimize import curve_fit

# ----------------------------
# Measured solenoid data
# ----------------------------
t = np.array([1, 2, 3, 4, 5, 8, 10, 20], dtype=float)

v = np.array([
    50,
    (95 + 100) / 2,      # 2 sec
    (140 + 145) / 2,    # 3 sec
    170,
    200,
    (300 + 310) / 2,    # 8 sec
    (400 + 425) / 2,    # 10 sec
    800
], dtype=float)

# ----------------------------
# Models to test
# ----------------------------
models = {
    "linear": lambda t, a, b: a * t + b,
    "quadratic": lambda t, a, b, c: a * t**2 + b * t + c,
    "power": lambda t, k, n: k * t**n,
}

best = None
lowest_error = float("inf")

# ----------------------------
# Fit and evaluate models
# ----------------------------
for name, model in models.items():
    try:
        params, _ = curve_fit(model, t, v, maxfev=10000)
        error = np.mean((model(t, *params) - v) ** 2)

        if error < lowest_error:
            best = (name, params)
            lowest_error = error
    except Exception as e:
        print(f"{name} failed:", e)

# ----------------------------
# Results
# ----------------------------
print("Best model:", best[0])
print("Parameters:", best[1])
print("Mean squared error:", lowest_error)

# ----------------------------
# Pretty-print formula
# ----------------------------
if best[0] == "linear":
    a, b = best[1]
    print(f"Formula: Volume = {a:.4f} * time + {b:.4f}")

elif best[0] == "quadratic":
    a, b, c = best[1]
    print(f"Formula: Volume = {a:.4f} * time^2 + {b:.4f} * time + {c:.4f}")

elif best[0] == "power":
    k, n = best[1]
    print(f"Formula: Volume = {k:.4f} * time^{n:.4f}")


import numpy as np

A = 0.11455309
B = 36.75567689
C0 = 19.817595

def time_from_volume(V_ml):
    disc = B*B - 4*A*(C0 - V_ml)
    if disc < 0:
        return None  # outside calibrated range

    t = (-B + np.sqrt(disc)) / (2*A)
    print(t)
    return t


