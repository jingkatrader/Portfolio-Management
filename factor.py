import pandas as pd
import numpy as np
import os
import time
import statsmodels.api as sm
import CONSTANT

def build_FF_factor_loading(y_df, FF_factor):
    y_df = y_df.dropna() # Regression cannot take Nan values
    overlap_timerange = y_df.index.intersection(FF_factor.index)
    reg = sm.OLS(y_df[overlap_timerange], FF_factor.loc[overlap_timerange]).fit()
    return reg


def build_asset_residual_from_FF_model(asset_return, FF_factor):
    asset_FF_resid = pd.DataFrame()
    for asset in asset_return.columns:
        reg = build_FF_factor_loading(asset_return[asset], FF_factor)
        asset_FF_resid = pd.concat([asset_FF_resid, pd.DataFrame(reg.resid, columns=[asset])], axis=1)
    return asset_FF_resid


def build_low_vol_bucket(residual_for_vol, rolling_period, min_period, decile):
    # benchmark on the rolling std on the FF3 factor residuals
    rolling_std = residual_for_vol.rolling(rolling_period, min_periods=min_period).std().resample('M').last()
    asset_bucket_combined = {}
    for idx, percentile in enumerate(decile):
        cut_off_percentile = rolling_std.quantile(percentile, axis=1)
        if idx == 0:
            asset_bucket = rolling_std.le(cut_off_percentile, axis=0).replace(False,
                                                                              np.nan)  # True only if asset vol <= target
        elif idx == len(decile) - 1:
            asset_bucket = rolling_std.gt(cut_off_percentile, axis=0).replace(False,
                                                                              np.nan)  # True only if asset vol > target
        else:
            prev_cut_off_percentile = rolling_std.quantile(decile[idx - 1], axis=1)
            asset_bucket = (
                        rolling_std.gt(prev_cut_off_percentile, axis=0) & rolling_std.le(cut_off_percentile, axis=0)) \
                .replace(False, np.nan)  # True only if prev_target < asset vol <= target
        asset_bucket_combined[percentile] = asset_bucket
    return asset_bucket_combined


def build_low_vol_factor(monthly_return, residual_for_vol, rolling_period, min_period, decile=[0.1, 0.9]):
    '''
    Assumes month end re-balance, bucket stock based on 1 month ahead waiting period, and 30 trading day rolling std,
    then, hold the stock portfolio for 1 month.
    :param monthly_return: monthly returns for individual stocks
    :param residual_for_vol: use each stock's idiosyncratic return from FF-3 factor model residual to assess vol bucket
    :param rolling_period: period of calculating stock vol
    :param min_period: min # of obs. to derive vol
    :param decile: list(cutoff vol percentiles to bucket stocks)
    :return:
    '''

    bucket_return_combined = pd.DataFrame()
    asset_bucket_combined = build_low_vol_bucket(residual_for_vol, rolling_period, min_period, decile)
    for percentile, asset_bucket in asset_bucket_combined.items():
        bucket_ret = asset_bucket.mul(monthly_return.resample('M').last()).mean(axis=1) #Equal weight bucket return
        bucket_return_combined = pd.concat([bucket_return_combined, bucket_ret.rename(percentile)], axis=1)
    return bucket_return_combined


if __name__ == "__main__":
    # Load the daily FF 3 factors, Mkt, SMB, HML
    FF_factor = pd.read_csv(os.path.join(CONSTANT.FF_PATH, 'F-F_Research_Data_Factors_daily.CSV'), skiprows=4, index_col= 0)
    FF_factor = FF_factor.iloc[:-1, :-1] # remove last row "Copyright" and last col "Rf"
    FF_factor.index = pd.to_datetime(FF_factor.index)

    US_stocks = pd.read_pickle("Single names prices-agg.pickle")
    US_stocks.drop(['HVT','COHR'],axis=1,inplace=True)

    US_stocks_ret = US_stocks.pct_change()

    t = time.time()
    US_stocks_residuals = build_asset_residual_from_FF_model(US_stocks_ret, FF_factor)
    print(f"took {round(time.time()-t, 2)} seconds to build residuals")
    US_stocks_residuals.to_pickle("Single names residuals.pickle")


    US_stocks_residuals = pd.read_pickle("Single names residuals.pickle")

    # Test factor using only NYSE stocks (Fewer small cap stocks)
    NYSE_stocks = pd.read_excel(os.path.join(CONSTANT.INPUT_PATH, "Single names-NYSE.xlsx"))['Trading Symbol'].to_list()
    NYSE_stocks_ret = US_stocks_ret[NYSE_stocks]
    NYSE_residuals = US_stocks_residuals[NYSE_stocks]
    NYSE_stocks_ret.to_pickle("NYSE ret.pickle")
    NYSE_residuals.to_pickle("NYSE residuals.pickle")

    NYSE_stocks_ret = pd.read_pickle("NYSE ret.pickle")
    NYSE_residuals = pd.read_pickle("NYSE residuals.pickle")
    NYSE_stocks_metadata = pd.read_pickle('NYSE stocks metadata.pickle')

    larger_than_1B = NYSE_stocks_metadata.T[NYSE_stocks_metadata.loc['MarketCapitalization'].astype(float) > 1000000000].index
    selected_stocks = NYSE_stocks_ret.loc['2020-01-01':, larger_than_1B].dropna(axis=1).columns #remove stocks only listed post-2020
    monthly_NYSE_ret = (1+NYSE_stocks_ret[selected_stocks]).resample('M').prod()-1
    bucket_return_combined = build_low_vol_factor(monthly_NYSE_ret, NYSE_residuals[selected_stocks].shift(22),
                                                  30, 15, [0.1, 0.3,0.7,0.9]) # shift by 22D to remove look-ahead bias
    bucket_return_combined.index = pd.to_datetime(bucket_return_combined.index)
    bucket_return_combined.mean()*12
    bucket_return_combined.std()*(12**0.5)
    (bucket_return_combined.mean()*12)/(bucket_return_combined.std()*(12**0.5))



    #### ------------------------------------ BELOW ARE MANUAL TESTING ------------------------------------

    rolling_std = NYSE_residuals.rolling(30, min_periods=15).std().resample('M').last()
    rolling_std = rolling_std[rolling_std.loc['2020-01-01':].dropna(axis=1).columns]
    median_std = rolling_std.median(axis=1)
    top10th_std = rolling_std.quantile(0.1, axis=1)
    bot10th_std = rolling_std.quantile(0.9, axis=1)
    p20_std = rolling_std.quantile(0.2, axis=1)
    p40_std = rolling_std.quantile(0.4, axis=1)
    p60_std = rolling_std.quantile(0.6, axis=1)
    p80_std = rolling_std.quantile(0.8, axis=1)

    p20_bucket = rolling_std.le(p20_std,axis=0).replace(False, np.nan)
    p40_bucket = (rolling_std.gt(p20_std,axis=0)&rolling_std.le(p40_std,axis=0)).replace(False, np.nan)
    p60_bucket = rolling_std.le(p60_std,axis=0).replace(False, np.nan)
    p80_bucket = rolling_std.le(p80_std,axis=0).replace(False, np.nan)
    p100_bucket = rolling_std.gt(p80_std,axis=0).replace(False, np.nan)

    p20_bucket.iloc[-1].sum()
    p40_bucket.iloc[-1].sum()

    low_vol_bucket = rolling_std.le(top10th_std,axis=0).replace(False, np.nan)
    high_vol_bucket = rolling_std.gt(bot10th_std,axis=0).replace(False, np.nan)
    low_vol_bucket_ret = low_vol_bucket.mul(NYSE_stocks_ret).mean(axis=1)
    high_vol_bucket_ret = high_vol_bucket.mul(NYSE_stocks_ret).mean(axis=1)
    low_vol_factor_ret = low_vol_bucket_ret - high_vol_bucket_ret


    low_vol_bucket_ret.mean() * (12)
    low_vol_bucket_ret.std() * np.sqrt(12)
    high_vol_bucket_ret.mean() * (12)
    high_vol_bucket_ret.std() * np.sqrt(12)


    monthly_ret = (1+US_stocks_ret).resample('M').prod()-1
    low_vol_bucket_ret_M = (low_vol_bucket.resample('M').last()).mul(monthly_ret).mean(axis=1)
    high_vol_bucket_ret_M = high_vol_bucket.resample('M').last().mul(monthly_ret).mean(axis=1)

    low_vol_factor_ret_M = low_vol_bucket_ret_M - high_vol_bucket_ret_M

