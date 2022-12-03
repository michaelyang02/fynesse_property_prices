from . import assess

import random
import numpy as np
import sklearn
from IPython.display import display


def predict_price(latitude, longitude, date, property_type):
    return predict_price_spec(latitude, longitude, date, property_type)


def predict_price_spec(latitude, longitude, date, property_type, boxsize=0.09, radius=0.09, half_days=1800, sample_size=100):
    model = sklearn.linear_model.LinearRegression(fit_intercept=False)

    labelled_data = assess.labelled(latitude, longitude, date, property_type, boxsize, radius, half_days)

    model.fit(labelled_data[0][:-1], labelled_data[1])
    coef = model.coef_
    print("Fitted model coefficients:\n")
    print(coef.reshape(-1, 1))

    squared_sum = 0
    for _ in range(0, sample_size):
        rand = random.randrange(0, labelled_data[0].shape[0] - 1)
        predicted_price = int(round(model.predict(labelled_data[0][rand].reshape(1, -1))[0], -3))
        real_price = labelled_data[1][rand]
        squared = ((predicted_price - real_price) / 100000) ** 2
        squared_sum += squared

    print(f"\nAverage {sample_size} normalised squared residuals: \t{squared_sum / sample_size:.2f}")

    print("\nPredicted property price:\n")
    [pred] = model.predict(labelled_data[0][-1].reshape(1, -1))
    print(int(pred))
    return int(pred)

