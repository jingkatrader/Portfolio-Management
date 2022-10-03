import pandas as pd
import numpy as np
import os
import time
import CONSTANT
import factor
import requests

# Test factor using only NYSE stocks (Fewer small cap stocks)
NYSE_stocks_ret = pd.read_pickle("NYSE ret.pickle")
NYSE_residuals = pd.read_pickle("NYSE residuals.pickle")
NYSE_stocks_metadata = pd.read_pickle('NYSE stocks metadata.pickle')

larger_than_1B = NYSE_stocks_metadata.T[NYSE_stocks_metadata.loc['MarketCapitalization'].astype(float) > 1000000000].index
selected_stocks = NYSE_stocks_ret.loc['2020-01-01':, larger_than_1B].dropna(axis=1).columns #remove stocks only listed post-2020


low_vol_stocks = factor.build_low_vol_bucket(NYSE_residuals[selected_stocks].shift(22), 30, 15, [0.1])
low_vol_stocks_names = low_vol_stocks[0.1].iloc[-1].dropna().index.to_list()
low_vol_stocks_names.remove('Y')

low_vol_stocks_ret = NYSE_stocks_ret[low_vol_stocks_names]
low_vol_stocks_std = low_vol_stocks_ret.rolling(30, min_periods=15).std()
low_vol_stocks_inv_vol_weight = (1/low_vol_stocks_std.iloc[-1])/(1/low_vol_stocks_std.iloc[-1]).sum()
low_vol_stocks_cov = low_vol_stocks_ret.cov()

# Inverse vol portfolio vol and ex-ante daily return
low_vol_stocks_inv_vol_weight.T@low_vol_stocks_cov@low_vol_stocks_inv_vol_weight
(1+(low_vol_stocks_ret.loc['2022-01-01':]@low_vol_stocks_inv_vol_weight)).prod()

# Equal weight portfolio vol
low_vol_stocks_ret.mean(axis=1).std()

# Show the number of stocks per sector
NYSE_stocks_metadata[larger_than_1B].T.groupby('Sector').count()