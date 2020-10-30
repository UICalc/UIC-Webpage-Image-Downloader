import time
import  requests
from bs4 import  BeautifulSoup
import os
import threading
from requests.adapters import HTTPAdapter
import re
from urllib import parse
from urllib.parse import unquote
import numpy as np

f=open(r'cookies.txt','r')#打开所保存的cookies内容文件
cookies={}#初始化cookies字典变量
for line in f.read().split(';'):   #按照字符：进行划分读取
    #其设置为1就会把字符串拆分成2份
    name,value=line.strip().split('=',1)
    cookies[name]=value  #为字典cookies添加内容
f.close()

hd = {'user-agent':'chorme/10'}
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://localhost:7890'}
dir_name = 'default'    #设置文件夹的名字
total_image = 0
done_image = 0
tot_error = 0

def getHTML(url):
    try:
        r = requests.get(url,timeout = 30,headers = hd, proxies = proxies, cookies = cookies)
        so = BeautifulSoup(r.text, 'lxml')
        r.raise_for_status()       #容错机制，若请求访问失败则返回的不是200，则返回字符串空
        if r.status_code != 200:
            print("Cannot access website.")
        r.encoding = r.apparent_encoding     #设置编码方式，用解析返回网页源码得出的编码方式代替  UTF-8
        global dir_name
        dir_name = so.title.text
        dir_name = re.sub(r'[\/:*?"<>|]', '', dir_name[0:255])
        print("Images will be saved to " + dir_name)
        return r.text
    except:
        return ''

def get_file_name(url, headers):
    filename = ''
    if 'Content-Disposition' in headers and headers['Content-Disposition']:
        disposition_split = headers['Content-Disposition'].split(';')
        if len(disposition_split) > 1:
            if disposition_split[1].strip().lower().startswith('filename='):
                file_name = disposition_split[1].split('=')
                if len(file_name) > 1:
                    filename = unquote(file_name[1])
    if not filename and os.path.basename(url):
        filename = os.path.basename(url).split("?")[0]
    if not filename:
        return time.time()
    return filename

def save_image(img_url):
    print("Downloading image in " + img_url)
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=5))
    s.mount('https://', HTTPAdapter(max_retries=5))
    
    try:
        response = s.get(img_url, headers = hd, proxies = proxies, timeout = 15, cookies = cookies)
        file_size_str = response.headers['Content-Length']
        file_size = int(file_size_str) / 1024
    except requests.exceptions.RequestException as e:
        print(e)
        tmpname = re.sub(r'[\/:*?"<>|]', '', img_url)[0:255]
        f = open(tmpname + '.txt', 'a+')
        f.write('ERROR when downloading ' + img_url + '\n')
        f.close
        f1 = open('log.txt', 'a+')
        f1.write('ERROR when downloading ' + img_url + '\n')
        f1.close
        global tot_error
        tot_error += 1
        return
    picture_name = get_file_name(img_url, response.headers)     #提取图片url后缀
    picture_name = re.sub(r'[\/:*?"<>|]', '', picture_name[0:255])
    filename = dir_name+'/'+picture_name
    new_count = 1
    if(os.path.exists(filename)):#文件已经存在咋办
        t = filename.rsplit('.', 1)
        if np.size(t) == 1:
            while os.path.exists(t[0] + '(' + str(new_count) + ')'):
                new_count = new_count + 1
            filename = t[0] + '(' + str(new_count) + ')'
        else:
            while os.path.exists(t[0] + '(' + str(new_count) + ').' + t[1]):
                new_count = new_count + 1
            filename = t[0] + '(' + str(new_count) + ').' + t[1]

    with open(filename,'wb') as f:
        f.write(response.content)

    global done_image
    global total_image
    done_image = done_image + 1
    print(filename + ' saved. (' + str(done_image) + '/' + str(total_image) + ')(' + str(file_size) + 'KB)')

def get_page(pageurl):
    url = pageurl    #爬取网页的url
    text = getHTML(url)
    soup = BeautifulSoup(text,'html.parser')
    a = soup.find_all('img')  #直接找出所有的img标签，观察发现每个图片的img标签并不一样，不能用正则表达式来统一查找
    urlInfo = []  #用来保存每一个图片拼接好的下载链接
    error = 0
    for tag in a:
        global total_image
        try:
            new_url = tag['src']    #得到img属性当中的src
            urlInfo.append(parse.urljoin(pageurl, new_url))
            #print('Waiting to download https://telegra.ph' + new_url)
            total_image = total_image + 1
        except:
            try:
                new_url = tag['data-src']
                urlInfo.append(parse.urljoin(pageurl, new_url))
                #print('Waiting to download https://telegra.ph' + new_url)
                total_image = total_image + 1
            except:
                error = error + 1
    #去除重复URL
    urlInfo = list(set(urlInfo))

    #保存图片，思路：将所有的图片保存在本地的一个文件夹下，用图片的url链接的后缀名来命名

    print(os.path)
    if not os.path.exists(dir_name):     #os模块判断并创建
        os.mkdir(dir_name)

    threads = []

    for img_url in urlInfo:
        i = 1
    #        time.sleep(1)   #设置间隔时间，防止把网页爬崩
        try:
            t = threading.Thread(target=save_image, args=(img_url,))
            threads.append(t)
            t.start()
            time.sleep(0.01)
        except:
            print("ERROR when creating thread")
        i = i + 1
    for t in threads:
        t.join()
    total_image = 0
    global done_image
    done_image = 0


f = open('downloads.txt')
line = f.readline()
downlist = []
downlisttmp = []
tot = 0
while line:
    if line[-1] == '\n':
        line = line[:-1]
    downlisttmp.append(line)
    line = f.readline()
repeated = 0
for i in downlisttmp:
    if i not in downlist:
        downlist.append(i)
        print('Download += ' + i)
    else:
        repeated += 1
tot = len(downlist)
print(str(repeated) + ' Repeated items removed.')
print('Download Started.')
t = 1
for downurl in downlist:
    print('Start to download ' + downurl + ' (' + str(t) + '/' + str(tot) + ')')
    get_page(downurl)
    print(downurl + ' downloaded. (' + str(t) + '/' + str(tot) + ')')
    t = t + 1
    f = open('downloaded.txt', "a+")
    f.write(downurl + '\n')
    f.close
print('Download Finished. ' + str(len(downlist)) + ' URL Downloaded. ' + str(tot_error) + ' Error(s) Occurred.')
f = open('downloads.txt', 'w')
f.close()