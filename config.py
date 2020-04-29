import os
os.environ['KERAS_BACKEND'] = 'tensorflow'

PATH_CNN_MODEL = 'cnn_captcha.json'
PATH_CNN_WEIGHTS = 'cnn_weights_captcha.h5'

PATH_IMG = 'img'
PATH_OUTPUT = '/data/dataset/TXO_transaction/'
# PATH_OUTPUT = '/home/cyyen/Downloads'
if not os.path.exists(PATH_OUTPUT):
    os.mkdir(PATH_OUTPUT)

PATH_CHROME_DRIVER = '/usr/local/bin/chromedriver'

from selenium.webdriver.chrome.options import Options
WIDTH_CHROME, HEIGHT_CHROME = 960, 1080
OPTIONS_CHROME = Options()
OPTIONS_CHROME.add_experimental_option("prefs", {"download.default_directory" : PATH_OUTPUT})
OPTIONS_CHROME.add_argument(f'--window-size={WIDTH_CHROME},{HEIGHT_CHROME}')

PATH_TMP_SCREENSHOT = 'screenshot.png'

URL_TARGET = "https://www.taifex.com.tw/cht/3/dailyOptions"


DIGIT_CAPTCHA = 6