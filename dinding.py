import base64
import hashlib
import hmac
import json
import socket
import sys
import threading
import time
from multiprocessing import Manager
from multiprocessing.context import Process
import urllib.parse
from pathlib import Path

import requests
dic_1 = {}
dic_2t = []
hashtab = {'一':0,'二':1,'三':2,'四':3,'五':4}
dic_text = ''
with open("input.txt", "r",encoding= 'utf-8') as f:
    temp = ''
    data = f.readlines()
    for item in data:
        if '+' in item:
            dic_text += item.split('+')[0] + '\n'
        else:
            dic_text += item
    for item in data:
        if item[0] in hashtab.keys():
            if temp != '':
                dic_1.update({temp:qs_temp})
                dic_2t.append(ans_temp)
            temp = item
            qs_temp = []
            ans_temp = []
        else:
            qs_temp.append(item.split('+')[0]+'\n')
            ans_temp.append(item.split('+')[1])
dic_1.update({temp:qs_temp})
dic_2t.append(ans_temp)
dic_2 = []
for item in dic_2t:
    dic_temp = {}
    for index in range(len(item)):
        dic_temp.update({str(index+1):item[index]})
    dic_2.append(dic_temp)
# print(dic_1,dic_2)
# with open("input.txt", "r") as f:  # 打开文件
#     dic_text = f.read()
# print(dic_text)
#
# hashtab = {'一':0,'二':1}
# dic_1 = {'一、self introduction':['1:who are you?\n','2:where are you from?\n'],'二、information':['1:informationA?\n','2:informationB?\n']}
# dic_2 = [{'1':'I am ming','2':'I come from CN'},{'1':'This is informationA','2':'This is informationB'}]

def handle_client(client_socket,usr_step):
    # 获取socket
    request_data = client_socket.recv(20000)
    post_userid, post_sign, post_timestamp, post_mes = getPost(request_data)
    # 回应socket
    initKey(post_userid, post_sign, post_timestamp, post_mes,usr_step)
    # 关闭socket
    client_socket.close()


def getPost(request_data):
    # 格式化socket数据
    request_data = str(request_data, encoding="utf8").split('\r\n')
    # print(request_data)
    items = []
    for item in request_data[1:-2]:
        items.append(item.split(':'))
    post_useful = dict(items)
    # print(post_useful)
    post_mes = json.loads(request_data[-1])
    post_sign = post_useful.get('sign').strip()
    post_timestamp = post_useful.get('timestamp').strip()
    post_userid = post_mes.get('senderId').strip()
    post_mes = post_mes.get('text').get('content').strip()
    return post_userid, post_sign, post_timestamp, post_mes


def initKey(post_userid, post_sign, post_timestamp, post_mes,usr_step):
    # 配置token,注意这里是你的机器人token
    whtoken="c243d37068d58b7328b2d8a0791d2bf7a99f6c63cd92ab9ec95974ff85b0fd58"
    # 得到当前时间戳
    timestamp = str(round(time.time() * 1000))
    # 计算签名，注意这里的secret是你机器人的appsecret而不是发送信息的那个secret
    app_secret = 'vm8lV1QSx__HVXVrHQZ-UfjDFLpkDmDlKjjwlFwUop65Jq_xDUrRXbVmVSwLmkd5'
    app_secret_enc = app_secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(post_timestamp, app_secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(app_secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    if (abs(int(post_timestamp) - int(timestamp)) < 3600000 and post_sign == sign):
        webhook = "https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign=".format(whtoken,timestamp,sign)
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        # 发送消息
        message_json = json.dumps(selectMes(post_userid, post_mes,usr_step))
        # 返回发送状态
        #这里的webhook就是上面的，但是secret是你测试群里的那个机器人签名secret
        send_webhook = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(whtoken)
        send_secret = 'SEC7e016c158e8b43ba71841c3110d5a47eac268d744ca8b636c71218b7c8fe108a'
        timestamp = str(round(time.time() * 1000))
        secret_enc = send_secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, send_secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        send_url = '{}&timestamp={}&sign={}'.format(send_webhook, timestamp, sign)
        info = requests.post(url=send_url, data=message_json, headers=header)
        # print(info.text)
    else:
        print("Warning:Not DingDing's post")

def load_qa():
    assert Path('QA.json').exists() == True
    with open('QA.json','r',encoding='utf-8') as f:
        qa = json.load(f)
        # print(qa)
    return qa


def selectMes(post_userid, post_mes,usr_step):
    # if post_userid not in usr_step.keys(): #如果用户id没有在usr_step列表里
    #     usr_step.update({post_userid:0})
    index = 0
    # print("nowstep",len(usr_step))
    text_temp = ''
    for item in dic_1.keys():
        if post_mes in item and post_mes != '':
            for i in dic_1.get(item):
                text_temp += i
            while len(usr_step) != 0:
                usr_step.pop()
            usr_step.append(1)
            usr_step.append(item)
            return sendText(post_userid, text_temp)
    if post_mes == '' or post_mes == '测试':
        # print('this is step1')
        while len(usr_step) > 1:
            usr_step.pop()
        return sendText(post_userid, dic_text)
    if len(post_mes) > 2:
        for item in dic_1.values():
            for i in range(len(item)):
                if post_mes in item[i][2:] and post_mes != '':
                    # print(index,i)
                    text_temp = dic_2[index].get(str(i+1))
                    # print(text_temp)
                    return sendText(post_userid, text_temp)
        index += 1
    if len(usr_step) == 1:
        # print('this is step2')
        text_temp = ''
        for item in dic_1.keys():
            if post_mes in item:
                for i in dic_1.get(item):
                    text_temp +=i
                usr_step.append(item)
                return sendText(post_userid, text_temp)
        usr_step.pop()
        return sendText(post_userid, dic_text)
    if len(usr_step) == 2:
        # print('this is step3')
        # print('usr_step[-1]',usr_step[-1])
        hashtab.get(usr_step[-1][0])
        if post_mes in dic_2[hashtab.get(usr_step[-1][0])].keys():
            text_temp = dic_2[hashtab.get(usr_step[-1][0])].get(post_mes)
            return sendText(post_userid, text_temp)
        else:
            usr_step.pop()
            return sendText(post_userid, dic_text)
    # if usr_step == 2:

    # qa = load_qa()
    # for key in qa:
    #     # print(f'key:{key} message in key:{message in  key}')
    #     if post_mes in key:
    #         # print(message)
    #         return sendText(post_userid, qa[key])
    # return sendText(post_userid, dic_text)


def sendText(post_userid, send_mes):
    # 发送文本形式
    message = {
        "msgtype": "text",
        "text": {
            "content": send_mes
        },
        "at": {
            "atDingtalkIds": [post_userid],
            "isAtAll": False
        }
    }
    return message


if __name__ == "__main__":
    manager = Manager()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", 8080))
    server_socket.listen(120)
    usr_step = manager.list()
    while True:
        client_socket, client_address = server_socket.accept()
        # print(client_address)
        handle_client_process = Process(target=handle_client, args=(client_socket,usr_step))
        handle_client_process.start()
        client_socket.close()