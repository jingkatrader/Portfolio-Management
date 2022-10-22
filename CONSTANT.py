import os
# get current directory
current_dir = os.getcwd()
# parent directory
DATA_FOLDER = 'Portfolio Data'
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir, DATA_FOLDER))

ETF_PRICE_DIR = os.path.join(parent_dir, 'Historical ETF prices')
SINGLE_NAME_DIR = os.path.join(parent_dir, 'Historical single name prices')
SINGLE_NAME_METADATA_DIR = os.path.join(parent_dir, 'Single name metadata')
INPUT_PATH = 'INPUT_cfg'
FF_PATH = os.path.join(parent_dir, 'FF-3factor')
TRADING_DIR_LOW_VOL = os.path.join(parent_dir, 'Trading_low_vol')
TRADING_DIR_LONG_SHORT = os.path.join(parent_dir, 'Trading_high_vol')


