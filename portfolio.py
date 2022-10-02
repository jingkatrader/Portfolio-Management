import pandas as pd
import numpy as np
import os
import time
import CONSTANT
import factor


# Test factor using only NYSE stocks (Fewer small cap stocks)
NYSE_stocks_ret = pd.read_pickle("NYSE ret.pickle")
NYSE_residuals = pd.read_pickle("NYSE residuals.pickle")


selected_stocks = NYSE_stocks_ret.loc['2020-01-01':].dropna(axis=1).columns #remove stocks only listed post-2020
monthly_NYSE_ret = (1+NYSE_stocks_ret[selected_stocks]).resample('M').prod()-1

low_vol_stocks = factor.build_low_vol_bucket(NYSE_residuals[selected_stocks].shift(22), 30, 15, [0.1])
low_vol_stocks_names = low_vol_stocks[0.1].iloc[-1].dropna().index.to_list()
low_vol_stocks_ret = NYSE_stocks_ret[low_vol_stocks_names]

low_vol_stocks_std = low_vol_stocks_ret.rolling(30, min_periods=15).std()
low_vol_stocks_inv_vol_weight = (1/low_vol_stocks_std.iloc[-1])/(1/low_vol_stocks_std.iloc[-1]).sum()