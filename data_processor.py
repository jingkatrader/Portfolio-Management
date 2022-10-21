import pandas as pd
import numpy as np
import os
import requests
import time
import CONSTANT


def download_asset_price(tickers, output_dir):
    overload_counter = 0
    t = time.time()
    for ticker in tickers:
        overload_counter += 1
        if overload_counter == 100:
            elaspsed_time = round(time.time() - t, 2)
            print(f"Took {elaspsed_time} to download 100 assets...")
            if elaspsed_time < 50:
                print("Taking a 1-min nap...Zzzzz")
                time.sleep(60)
            else:
                time.sleep(10)
            t = time.time()
            overload_counter = 1
        # ticker = 'HVTA'
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey=1Z1KIUWET1356LLE'
        r = requests.get(url)
        data = r.json()
        try:
            prices = pd.DataFrame(data['Time Series (Daily)'])
            prices = prices.T.sort_index(ascending=True)
            prices.index = pd.to_datetime(prices.index)
            prices.to_pickle(os.path.join(output_dir, f'{ticker}.pickle'))
        except:
            print(f"{ticker} is invalid please remove from the asset list")


def download_asset_metadata(tickers, output_dir):
    overload_counter = 0
    t = time.time()
    for ticker in tickers:
        overload_counter += 1
        if overload_counter == 100:
            elaspsed_time = round(time.time() - t, 2)
            print(f"Took {elaspsed_time} to download 100 assets...")
            if elaspsed_time < 50:
                print("Taking a 1-min nap...Zzzzz")
                time.sleep(60)
            else:
                time.sleep(10)
            t = time.time()
            overload_counter = 1
        # ticker = 'HVTA'
        url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey=1Z1KIUWET1356LLE'
        r = requests.get(url)
        data = r.json()
        try:
            metadata = pd.DataFrame(data, index=[0]).T
            metadata.to_pickle(os.path.join(output_dir, f'{ticker}.pickle'))
        except:
            print(f"{ticker} is invalid please remove from the asset list")


def load_asset_price(data_path):
    asset_prices = pd.DataFrame()
    for asset in os.listdir(data_path):
        if not asset.startswith('.') and os.path.isfile(os.path.join(data_path, asset)):
            asset_price = pd.read_pickle(os.path.join(data_path, asset))
            asset_prices = pd.concat([asset_prices, asset_price['4. close'].rename(asset.split('.')[0])], axis=1)
    asset_prices.sort_index(ascending=True, inplace=True)
    asset_prices.index = pd.to_datetime(asset_prices.index)
    try:
        asset_prices = asset_prices.astype('float')
    except:
        print('Unable to convert some asset prices into float...')
    return asset_prices


def load_asset_metadata(data_path):
    asset_metadata_combined = pd.DataFrame()
    for asset in os.listdir(data_path):
        if not asset.startswith('.') and os.path.isfile(os.path.join(data_path, asset)):
            asset_metadata = pd.read_pickle(os.path.join(data_path, asset))
            asset_metadata_combined = pd.concat([asset_metadata_combined, asset_metadata.rename(columns={0: asset.split('.')[0]})], axis=1)

    return asset_metadata_combined

if __name__ == "__main__":
    # Download ETF prices
    ETFs_metadata = pd.read_excel(os.path.join(CONSTANT.INPUT_PATH, "Investable List.xlsx"))
    ETFs_ticker = ETFs_metadata.query("Country != 'CA'")['ETF_ID']
    US_ETF = load_asset_price(CONSTANT.ETF_PRICE_DIR)

    # Download US Single names from NYSE, AMEX and NASDAQ
    single_names_metadata = pd.read_excel(os.path.join(CONSTANT.INPUT_PATH, "Single names.xlsx"))
    single_names_ticker = single_names_metadata['Trading Symbol']
    download_asset_price(single_names_ticker, CONSTANT.SINGLE_NAME_DIR)

    # Combine all single names from local
    US_stocks = load_asset_price(CONSTANT.SINGLE_NAME_DIR)
    US_stocks = US_stocks.astype('float')
    US_stocks.index = pd.to_datetime(US_stocks.index)
    # TODO remember to check duplicated column next time
    # Save cache for faster loading next time
    US_stocks.to_pickle("Single names prices-agg.pickle")

    US_stocks = pd.read_pickle("Single names prices-agg.pickle")  # This is temp code, change to US stocks next time
    US_stocks.drop(['HVT', 'COHR'], axis=1, inplace=True)

    # Download all metadata for NYSE stocks
    NYSE_stocks = pd.read_excel(os.path.join(CONSTANT.INPUT_PATH, "Single names-NYSE.xlsx"))['Trading Symbol'].to_list()
    download_asset_metadata(NYSE_stocks, CONSTANT.SINGLE_NAME_METADATA_DIR)
    NYSE_stocks_metadata = load_asset_metadata(CONSTANT.SINGLE_NAME_METADATA_DIR)
    NYSE_stocks_metadata.to_pickle('NYSE stocks metadata.pickle')

    # download_asset_price(remove.iloc[:,0], SINGLE_NAME_DIR)
    # remove = US_stocks.columns[US_stocks.iloc[-1].isna()] #remove the stocks delisted as of last day
    # single_names_metadata[~single_names_metadata['Trading Symbol'].isin(remove)].to_excel('Single names.xlsx')

    ## Remove the acquisition funds SPACs
    # single_names_metadata[~single_names_metadata['Company Name'].str.contains('ACQUISITION')].to_excel('Single names.xlsx')

    # # ------------------------- Other API calls from Alpha Vantage   ------------------------------
    #
    url = 'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=ED&outputsize=full&apikey=1Z1KIUWET1356LLE'
    r = requests.get(url)
    data = r.json()
    annual_report = pd.DataFrame(data['annualReports'])
    quarterly_report = pd.DataFrame(data['quarterlyReports'])
    #
    # # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
    # url = 'https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=CAD&apikey=1Z1KIUWET1356LLE'
    # r = requests.get(url)
    # data = r.json()
    # data['Realtime Currency Exchange Rate']
    #
    # url = 'https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&outputsize=full&apikey=1Z1KIUWET1356LLE'
    # r = requests.get(url)
    # data = r.json()
    # prices = pd.DataFrame(data['Time Series (Digital Currency Daily)'])
    #
    # # download TSX prices, but only available for one year
    # url = "http://api.marketstack.com/v1/eod?access_key=18647bf3eade7aabc046ef220b476e2f&symbols=XIU.XTSE"
    # r = requests.get(url)
    # data = r.json()
    # prices = pd.DataFrame(data['data'])

    ticker = 'COHR'
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey=1Z1KIUWET1356LLE'
    r = requests.get(url)
    data = r.json()
    prices = pd.DataFrame(data['Time Series (Daily)'])
    prices = prices.T.sort_index(ascending=True)
    prices.index = pd.to_datetime(prices.index)




