import pandas as pd
import numpy as np

import requests

# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=TLT&outputsize=full&apikey=1Z1KIUWET1356LLE'
r = requests.get(url)
data = r.json()

print(data)

