
import os
import matplotlib.pylab as plt
import imageio
from PIL import Image 
import numpy as np
from tqdm import tqdm
import time


# In[4]:


import config as cfg
from captcha_predict import captcha_rec


# In[5]:


from pyvirtualdisplay import Display


# In[6]:


from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import StaleElementReferenceException, UnexpectedAlertPresentException, NoSuchElementException


# In[7]:


# reference: http://allselenium.info/capture-screenshot-element-using-python-selenium-webdriver/
def get_capture_img(driver, debug=False):
    # save screenshot
    fname = cfg.PATH_TMP_SCREENSHOT
    if os.path.exists(fname):
        os.remove(fname)
    driver.save_screenshot(fname)
    
    # get location of captcha img
    element = driver.find_element_by_id("captchaImg")
    location = element.location
    size = element.size
    
    original_size = driver.get_window_size()
    screenshot_size = imageio.imread(fname).shape
    if debug:
        print(f'size of Chrome: {original_size}')
        print(f'size of screeenshot: ({screenshot_size[1]},{screenshot_size[0]},{screenshot_size[2]})')    
        print(f'location: {location}')
        print(f'size: {size}')
    
    x, y = location['x'], location['y']
    x_end, y_end = x + size['width'], y + size['height']

    img = Image.open(fname)
    img_captcha = img.crop((int(x), int(y), int(x_end), int(y_end)))
    return np.array(img_captcha)[:,:,:3]

def collect_captcha_img(n=10):
    with webdriver.Chrome(executable_path = cfg.PATH_CHROME_DRIVER, options=cfg.OPTIONS_CHROME) as driver:
        for i in tqdm(range(n)):
            driver.get(cfg.URL_TARGET)

            img_captcha = get_capture_img(driver)
            plt.imshow(img_captcha)
            plt.show()

            captcha = input('Please enter 6-digit numbers in the captcha:')
            print(captcha)

            imageio.imwrite(f'{cfg.PATH_IMG}/{captcha}.png', img_captcha)


# In[8]:


# collect_captcha_img(2)


# In[14]:


def try_until_success(func):
    def wrapped_func(*args, **kwargs):    
        MAX_FAIL = 10
        n_fail = 0
        
        def print_fail_msg():
            print(f'The {n_fail}-th failure: {args}')
            time.sleep(1)
            
        while n_fail < MAX_FAIL:
            try:
                func(*args, **kwargs)
                print(f'Success: {args}')
                break
            except StaleElementReferenceException:
                print_fail_msg()
            except NoSuchElementException:
                print_fail_msg()
            except UnexpectedAlertPresentException:
                print_fail_msg()
            n_fail+=1
    return wrapped_func

def get_expected_filename(driver, form_values):
    form_values = dict(form_values)
    filename = 'AH_' if form_values['MarketCode'] == '1' else ''
    date_id = 'queryDateAh' if form_values['MarketCode'] == '1' else 'queryDate'
    date_download = driver.find_element_by_xpath(f"//input[@id='{date_id}']").get_attribute('value')
    filename += f'{date_download}_{form_values["commodity_idt"]}_{form_values["settlemon"]}_{form_values["pccode"]}.csv'
    return filename

@try_until_success
def select_option_by_id(driver, id_select, option):
    Select(driver.find_element_by_id(id_select)).select_by_value(option)
    
@try_until_success
def download_daily_option_transaction(driver, form_values, debug=False):
    driver.get(cfg.URL_TARGET)
    
    # submit form
    img_captcha = get_capture_img(driver)
    captcha = captcha_rec.captcha_predict(captcha_rec.preprocess(img_captcha))
    
    for select_id, option_value in form_values:
        select_option_by_id(driver, select_id, option_value)
    driver.find_element_by_id('captcha').send_keys(captcha)
    
    submit = driver.find_element_by_xpath("//form[@id='uForm']//input[@id='button'][1]")
    submit.click()
    
    # download
    expected_fname = cfg.PATH_OUTPUT + '/' + get_expected_filename(driver, form_values)
    if os.path.exists(expected_fname):
        os.remove(expected_fname)
    download = driver.find_element_by_xpath("//form[@id='uForm']//input[@id='button'][2]")
    download.click()
    time.sleep(10)
    
    # TODO:if switch to TGO, then data may be empty and therefore the infinite while loop will be endles
    i = 0
    while not os.path.exists(expected_fname):
        time.sleep(3)
        print(f'Downloading... Not yet found {expected_fname} ')
        i+=1
        if i > 10:
            break
    if debug:
        print('finish downloading option transaction data')
    
    # save correct captcha images
    imageio.imwrite(f'{cfg.PATH_IMG}/{captcha}.png', img_captcha)
    if debug:
        print('saved captcha image')


# In[15]:


# get all form values
def get_settlemons(driver, commodity_idt):
    def get_random_settlemon(driver):
        date0 = driver.find_element_by_xpath(f"//input[@id='queryDate']").get_attribute('value')
        date1 = driver.find_element_by_xpath(f"//input[@id='queryDateAh']").get_attribute('value')
        date = max(date0, date1)
        return str(int(date[:6]) + 1)
    
    form = (
        ('MarketCode', '0'),
        ('commodity_idt', commodity_idt),
        ('settlemon', get_random_settlemon(driver)),
    )
    
    for select_id, option_value in form:
        select_option_by_id(driver, select_id, option_value)
    values = [ elem.get_attribute('value') for elem in driver.find_elements_by_xpath("//select[@id='settlemon']/option")]
    return [val for val in values if val != '']

# def get_commodity_ids(driver):# TODO: STO
#     random_commodity_idt = 'TXO'
#     form = {
#         'MarketCode': '0',
#         'commodity_idt': random_commodity_idt,
#     }
#     for select_id, option_value in form.items():
#         select_option_by_id(driver, select_id, option_value)
#     values = [ elem.get_attribute('value') for elem in driver.find_elements_by_xpath("//select[@id='commodity_idt']/option")]
#     return [val for val in values if val != '']

def get_all_forms(driver):
    driver.get(cfg.URL_TARGET)
    form = {
        'commodity_idt': 'TXO', #TODO: get_commodity_ids(driver)
    }

    marketcodes = ['0', '1']
    settlemons = get_settlemons(driver, commodity_idt=form['commodity_idt'])
    settlemons.sort(reverse=True) # in order to download monthly option first then weekly
    pccodes = ['C', 'P']
    forms = [
        (
            ('MarketCode', marketcode),
            ('commodity_idt', form['commodity_idt']),
            ('settlemon', settlemon),
            ('pccode', pccode),
        ) 
        for marketcode in marketcodes
        for settlemon in settlemons 
        for pccode in pccodes
    ]
    return forms


# In[16]:


display = Display(visible=0, size=(cfg.WIDTH_CHROME+20, cfg.HEIGHT_CHROME+20)) # for some reason, the size of display will be 20 less. To compensate it, we add 20 back
display.start() 

with webdriver.Chrome(executable_path = cfg.PATH_CHROME_DRIVER, options=cfg.OPTIONS_CHROME) as driver:
    driver.get(cfg.URL_TARGET)
    forms = get_all_forms(driver)
    for form in tqdm(forms):
        download_daily_option_transaction(driver, form, debug=True)

