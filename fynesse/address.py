from .config import *
from . import assess
from .utils import *

import sklearn


def predict_price(latitude, longitude, date, property_type):
    print("Fitting model...\n")
    model = sklearn.linear_model.LinearRegression(fit_intercept=False)
    labelled_data = assess.labelled(latitude, longitude, 0.09, 0.09)

    model.fit(labelled_data[0], labelled_data[1])
    coef = model.coef_
    print("Fitted model coefficients:\n")
    print(coef)

    pred = model.predict(labelled_data[3])
    print(pred)

