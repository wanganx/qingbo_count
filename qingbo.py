# -*- coding:utf-8 -*-
import json
import time
import requests
import pandas as pd
from sklearn.externals import joblib
import datetime
import os
import codecs
import uuid
import matplotlib.pyplot as plt
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from settings import QINGBO_USERNAME,QINGBO_PASSWORD
import bs4

# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')
# from Common.proxy_manager import get_a_proxy_dict_for_requests

# 代理服务器
proxy_host = "proxy.abuyun.com"
proxy_port = "9020"

# 代理隧道验证信息
proxy_user = "H21OAALA4NOK0K0D"
proxy_pass = "45BDAA08611DBFCF"

proxy_meta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": proxy_host,
    "port": proxy_port,
    "user": proxy_user,
    "pass": proxy_pass,
}

proxy_handler = {
    "http": proxy_meta,
    "https": proxy_meta,
}

def get_a_proxy_dict_for_requests():
    return proxy_handler
if not os.path.exists('cookie'):
    os.mkdir('cookie')
cookie_path = 'cookie/qingbo_cookie.dat'
s = requests.Session()
def s_get(url,params=None,headers=None):
    global s
    if not os.path.exists(cookie_path):
        qingbo = Qingbo()
        qingbo.login_in()
    with open(cookie_path,'r') as f:
        s.cookies.clear()
        for line in f.readlines():
            cookie = json.loads(line)
            c = {cookie['name']:cookie['value']}
            requests.utils.add_dict_to_cookiejar(s.cookies,c)
    for retry in range(5):
        try:
            req = s.get(url,params=params,headers=headers)
            return req
        except Exception as e:
            print(e)
            time.sleep(3)


predict_model = joblib.load('learn_model/little_num.svm')

#读取图片文件并切割文字
def get_num_img(img_path):
    img = plt.imread(img_path).mean(axis=2)
    test_list = []
    img_test_list = []
    start = 0
    while True:
        flag = 0
        if (img[:, start] == 1).all():
            j = 10
        else:
            j = 9
        for i in range(j):
            if (img[:, start + i] == 1).all():
                #                 print(img[:,start+i])
                #                 print(flag)
                if i < 3:
                    flag += 1
                else:
                    break

        if flag == 3:
            # print ('down')
            break

        c = img[:, start + flag:start + i]
        if (c == 1).all():
            # print ('stop')
            break
            #         print(c.size)
        C = np.ones(shape=(10, 1))
        if c.size == 70:
            c = np.concatenate([c, C], axis=1)
            # print('plus')
        if c.size == 60:
            c = np.concatenate([c, C, C], axis=1)
            # print('plus2')
        if c.size == 50:
            c = np.concatenate([c, C, C, C], axis=1)
            # print('plus3')
        # print(c.size)
        test_list.append(c.reshape(-1))
        img_test_list.append(c)
        start = start + i
    return test_list

#通过url 获取识别图片上的数字
def get_num_for_img(url):
    if url == '/query/drawcaptcha?num=MQTBBDXSKJwqO0O0OiO0O0On':
        return '10W+'
    temp_path = 'tem'
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    if 'http://www.gsdata.cn' not in url:
        url = 'http://www.gsdata.cn' + url
    req = requests.get(url)
    file_path = os.path.join(temp_path,str(uuid.uuid4())+'.png')
    with open(file_path,'wb') as f:
        f.write(req.content)
    this_num_list = get_num_img(file_path)
    x = predict_model.predict(this_num_list)
    os.remove(file_path)
    return ''.join(x)

#清博账号登录以及保存cookie
class Qingbo():
    url = 'http://www.gsdata.cn//member/login'

    def __init__(self):
        self.data_path = cookie_path
        if not os.path.exists('cookie'):
            os.makedirs(self.data_path)
        cap = webdriver.DesiredCapabilities.PHANTOMJS
        cap["phantomjs.page.settings.resourceTimeout"] = 1000

        # self.driver = webdriver.PhantomJS(desired_capabilities=cap)
        self.driver = webdriver.Chrome()
        self.driver.set_page_load_timeout(30)

    def __del__(self):
        self.driver.quit()

    def save_cookie_to_file(self):
        cookies = self.driver.get_cookies()
        # print cookies
        with codecs.open(cookie_path, mode='w+', encoding='utf-8') as f:
            for cookie in cookies:
                line = json.dumps(cookie, ensure_ascii=False) + '\n'
                f.write(line)

    def retry_get(self, url):
        for retry in range(3):
            try:
                self.driver.get(url)
                break
            except TimeoutException:
                self.driver.execute_script('window.stop()')


    def login_in(self):
        # try:
            self.retry_get(self.url)
            is_code = self.driver.find_element_by_xpath('//*[@id="wxLogin"]/p')
            print(is_code.text)
            if u'微信扫一扫' in is_code.text:
                user_log_button = self.driver.find_element_by_xpath('/html//div[contains(@class,"login-box")]/div[contains(@class,"login-body")]/a[@class="login-type current"]')
                print(user_log_button)
                user_log_button.click()
            uin_input = self.driver.find_element_by_name('username')
            uin_input.clear()
            uin_input.send_keys(QINGBO_USERNAME)
            pwd_input = self.driver.find_element_by_name("password")
            pwd_input.clear()
            pwd_input.send_keys(QINGBO_PASSWORD)
            pwd_input.send_keys(Keys.ENTER)
            self.save_cookie_to_file()
            self.__del__()
        # except Exception,e:
        #     print e

#获取一页信息并保存下来
def get_write_one_page(search_word,startTime,endTime,page):
    url = 'http://www.gsdata.cn/query/ajax_arc'
    params = {
        'q':search_word,
        'page':page,
        'types':'all',
        'industry':'all',
        'post_time':5,
        'startTime':startTime,
        'endTime':endTime,
        'sort':'readnum',
        'proName':'',
    }
    headers = {
        'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Connection':'keep-alive',
        'Host':'www.gsdata.cn',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'X-Requested-With':'XMLHttpRequest',
    }
    res = s_get(url,params=params,headers=headers)
    res_json = json.loads(res.text)
    # print res_json['data']
    if not res_json.get('data'):
        return None
    bsp = bs4.BeautifulSoup(res_json['data'],'lxml')
    with open(out_file,'a',encoding='utf8') as f:
        for li in bsp.find_all('li'):
            official_accounts = li.select('div > div.word > div > div.fl > a')[0].text
            title = li.select('div > div.word > h2 > a')[0].text
            read_num = '--'
            thump_up_num = '--'
            try:
                img_num = li.select('#captcha-img')
                if len(img_num) >=1:
                    read_num = get_num_for_img(img_num[0].get('src'))
                if len(img_num) >=2:
                    thump_up_num = get_num_for_img(img_num[1].get('src'))
            except:
                print('no read_num')

            date_ = li.select('div > div.word > div > div.fl > span')
            if date_:
                date = date_[0].text
            else:
                date = ''
            print (official_accounts,title,read_num,thump_up_num,date)
            f.write(official_accounts+'$'+title+'$'+read_num+'$'+thump_up_num+'$'+date+'\n')

def get_and_write_file(search_word, start_time, end_time,pages):
    startTime_ = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    endTime_ = datetime.datetime.strptime(end_time, '%Y-%m-%d')
    while startTime_ <= endTime_:
        startTime = startTime_.strftime('%Y-%m-%d')
        endTime = startTime
        startTime_ += datetime.timedelta(days=1)
        print('++++++++++++++' + startTime + '+++++++++++++')
        for page in range(1,pages+1):
            print('---------第' + str(page) + '页--------')
            try:
                get_write_one_page(search_word, startTime, endTime, page)
            except Exception as e:
                if e == 'data':
                    break
                try:
                    qingbo = Qingbo()
                    qingbo.login_in()
                    time.sleep(3)
                    get_write_one_page(search_word, startTime, endTime, page)
                except Exception as e:
                    print(e)
                    break
            time.sleep(3)
            to_excel(out_file)
def to_excel(file_path):
    big_df = pd.read_csv(file_path, sep='$', header=None, engine='python', encoding='utf8')
    big_df.columns = ['公众号', '文章名', '阅读量', '点赞数', '日期']
    big_df.to_excel(file_path.rsplit('.', 1)[0] + '.xlsx', index=False, encoding='utf8')


if __name__ == '__main__':
    out_file = 'data/test.csv'
    # out_file = 'data/test.csv'
    search_word = '复仇者联盟'
    start_time = '2018-05-08'
    end_time = '2018-05-08'
    #每查询一次的最大页数（正常用户下最少1页最大9页）
    pages = 9
    get_and_write_file(search_word,start_time,end_time,pages)