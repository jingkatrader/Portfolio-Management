import pandas as pd
import numpy as np
import os
import time
import CONSTANT
import factor
import requests
import data_processor


def form_inv_vol_weights(ret):
    low_vol_stocks_std = ret.rolling(30, min_periods=15).std()
    low_vol_stocks_inv_vol_weight = (1/low_vol_stocks_std.iloc[-1])/(1/low_vol_stocks_std.iloc[-1]).sum()
    return low_vol_stocks_inv_vol_weight


def report_portfolio_stats(ret, weights):
    # Inverse vol portfolio vol and ex-ante daily return
    cov = ret.cov()
    portfolio_vol = weights.T@cov@weights
    ex_ret = (1+(ret@weights)).prod() - 1
    ex_ret_post_2022 = (1 + (ret.loc['2022-01-01':] @ weights)).prod()
    return {'portfolio_vol' : portfolio_vol,
            "Expected_cum_return": ex_ret,
            'Expected_cum_return_post2022': ex_ret_post_2022
            }

if __name__ == "__main__":
    # Test factor using only NYSE stocks (Fewer small cap stocks)
    NYSE_residuals = pd.read_pickle("NYSE residuals.pickle")
    NYSE_stocks_metadata = pd.read_pickle('NYSE stocks metadata.pickle')

    # Remove the stocks that have <1B Mkt Cap or only start trading after 2020
    larger_than_1B = NYSE_stocks_metadata.T[NYSE_stocks_metadata.loc['MarketCapitalization'].astype(float) > 1000000000].index
    selected_stocks = NYSE_residuals.loc['2020-01-01':, larger_than_1B].dropna(axis=1).columns #remove stocks only listed post-2020

    # find the low vol stock names
    low_vol_stocks = factor.build_low_vol_bucket(NYSE_residuals[selected_stocks].shift(22), 30, 15, [0.1])
    low_vol_stocks_names = low_vol_stocks[0.1].iloc[-1].dropna().index.to_list()
    low_vol_stocks_names.remove('Y')

    # Find the highest vol stock names
    high_vol_stocks = factor.build_low_vol_bucket(NYSE_residuals[selected_stocks].shift(22), 30, 15, [0.1, 0.9])
    high_vol_stocks_names = high_vol_stocks[0.9].iloc[-1].dropna().index.to_list()
    high_vol_stocks_names.remove('AVLR')
    high_vol_stocks_names.remove('RFP')
    high_vol_stocks_names.remove('ZEN')

    # Download price for trading/re-balance for long-only low volatility portfolio
    data_processor.download_asset_price(low_vol_stocks_names, CONSTANT.TRADING_DIR_LOW_VOL)
    low_vol_stocks_price = data_processor.load_asset_price(CONSTANT.TRADING_DIR_LOW_VOL)
    low_vol_stocks_ret = low_vol_stocks_price.pct_change()
    low_vol_stocks_inv_vol_weight = form_inv_vol_weights(low_vol_stocks_ret)

    portfolio_summary_stats = report_portfolio_stats(low_vol_stocks_ret, low_vol_stocks_inv_vol_weight)

    # Export to trade book
    trading_book = pd.concat([low_vol_stocks_price.iloc[-1], low_vol_stocks_inv_vol_weight],axis=1)
    trading_book.columns = [f'Price as of {low_vol_stocks_price.index[-1].strftime("%Y-%m-%d")}', 'Weight']
    trading_book.sort_index(inplace=True)
    trading_book.to_clipboard()


    # Download price for trading/re-balance for long-short low-high volatility portfolio
    data_processor.download_asset_price(high_vol_stocks_names, CONSTANT.TRADING_DIR_LONG_SHORT)
    high_vol_stocks_price = data_processor.load_asset_price(CONSTANT.TRADING_DIR_LONG_SHORT)
    high_vol_stocks_ret = high_vol_stocks_price.pct_change()

    high_vol_stocks_inv_vol_weight = form_inv_vol_weights(high_vol_stocks_ret)

    portfolio_summary_stats = report_portfolio_stats(high_vol_stocks_ret, high_vol_stocks_inv_vol_weight)

    trading_book = pd.concat([high_vol_stocks_price.iloc[-1], high_vol_stocks_inv_vol_weight],axis=1)
    trading_book.columns = [f'Price as of {high_vol_stocks_price.index[-1].strftime("%Y-%m-%d")}', 'Weight']
    trading_book.sort_index(inplace=True)
    trading_book.to_clipboard()


    # Clean up the current order book from RPM
    current_book = pd.read_clipboard()
    current_book['Ticker_clean'] =[x[0] for x in current_book.iloc[:,0].str.split('-')]
    current_book.groupby('Ticker_clean').sum().to_clipboard()

    # Equal weight portfolio vol
    low_vol_stocks_ret.mean(axis=1).std()

    # Show the number of stocks per sector
    NYSE_stocks_metadata[larger_than_1B].T.groupby('Sector').count()

    low_vol_stocks_price.iloc[-1].to_clipboard()

    low_vol_stocks_inv_vol_weight.to_clipboard()

    # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
    url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=KO&interval=5min&apikey=1Z1KIUWET1356LLE'
    r = requests.get(url)
    data = r.json()


    # Leave this code for research purpose
    NYSE_stocks_ret = pd.read_pickle("NYSE ret.pickle") # This is full NYSE Stock returns
    low_vol_stocks_ret = NYSE_stocks_ret[low_vol_stocks_names]