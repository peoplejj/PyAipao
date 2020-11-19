import json
from random import randint, uniform
import os

import requests


def encrypt(number):
    key = "xfvdmyirsg"
    numbers = list(map(int, list(str(number))))
    return_key = "".join([key[i] for i in numbers])
    return return_key


# def pretty_print(jsonStr):
#     print(json.dumps(json.loads(jsonStr), indent=4, ensure_ascii=False))


class Aipaoer(object):
    def __init__(self, IMEICode):
        self.IMEICode = IMEICode
        self.userName = ""
        self.userId = ""
        self.schoolName = ""
        self.token = ""
        self.runId = ""
        self.distance = 2000
        self.minSpeed = 2.0
        self.maxSpeed = 3.0

    def __str__(self):
        return str(self.__dict__).replace("\'", "\"")

    def check_imeicode(self):
        IMEICode = self.IMEICode
        url = "http://client3.aipao.me/api/%7Btoken%7D/QM_Users/Login_AndroidSchool?IMEICode={IMEICode}".format(
            IMEICode=IMEICode)
        headers = {'version': '2.40'}
        rsp = requests.get(url, headers=headers)
        try:
            if rsp.json()["Success"]:
                okJson = rsp.json()
                self.token = okJson["Data"]["Token"]
                self.userId = okJson["Data"]["UserId"]
                return True
            else:
                return False
        except KeyError:
            print("IMEICode 失效")
            return False

    def get_info(self):
        token = self.token
        url = "http://client3.aipao.me/api/{token}/QM_Users/GS".format(
            token=token)
        headers = {'version': '2.40'}
        rsp = requests.get(url, headers=headers)
        try:
            if rsp.json()["Success"]:
                okJson = rsp.json()
                self.userName = okJson["Data"]["User"]["NickName"]
                self.schoolName = okJson["Data"]["SchoolRun"]["SchoolName"]
                self.minSpeed = okJson["Data"]["SchoolRun"]["MinSpeed"]
                self.maxSpeed = okJson["Data"]["SchoolRun"]["MaxSpeed"]
                self.distance = okJson["Data"]["SchoolRun"]["Lengths"]
        except KeyError:
            print("Unknown error in get_info")

    def get_runId(self):
        token = self.token
        distance = self.distance
        url = "http://client3.aipao.me/api/{token}/QM_Runs/SRS?S1=32.35011&S2=119.40146&S3={distance}" \
            .format(token=token, distance=distance)
        headers = {'version': '2.40'}
        rsp = requests.get(url, headers=headers)
        try:
            if rsp.json()["Success"]:
                self.runId = rsp.json()["Data"]["RunId"]
        except KeyError:
            print("Unknown error in get_runId")

    def upload_record(self):
        my_distance = self.distance + randint(0, 1)
        my_step = randint(950, 1250)
        my_speed = round(uniform(self.minSpeed + 0.3, self.maxSpeed - 1.5), 2)
        my_costTime = int(my_distance // my_speed)
        myParams = {
            "token": self.token,
            "runId": self.runId,
            "costTime": encrypt(my_costTime),
            "distance": encrypt(my_distance),
            "step": encrypt(my_step)}
        url = "http://client3.aipao.me/api/{token}/QM_Runs/ES?" \
              "S1={runId}&S4={costTime}&S5={distance}&S6=B4B1B0B4B3&S7=1&S8=xfvdmyirsg&S9={step}".format(
                  **myParams)
        headers = {'version': '2.40'}
        rsp = requests.get(url, headers=headers)
        try:
            if rsp.json()["Success"]:
                fin = {'msg': 'success',
                       'end': '|'+self.userName+'|'+str(my_speed)+'|'+str(my_distance) +
                       '|'+str(my_costTime)+'|'+str(my_step)+'|'
                       }
                return fin
        except KeyError:
            fin = {'msg': 'error'}
            return fin


def weixin_send(SCKEY, body):
    '''
    该函数的功能是向微信发送推送，通过server酱的接口实现\n
    SCKEY是向server酱表明身份的值，为字符串\n
    body是发送的内容，为字典，设有关建字【都为字符串】\n
        text：标题
        desp：正文\n
    发送成功返回True，反之为False
    '''
    url = "https://sc.ftqq.com/%s.send" % (SCKEY)
    r = requests.post(url, data=body)
    okJson = r.json()
    if (okJson["errmsg"] == "success"):
        return True
    else:
        return False


def main():
    ends = ["|姓名|&nbsp;速度&nbsp;|&nbsp;距离&nbsp;|&nbsp;时间&nbsp;|&nbsp;步数&nbsp;|",
            "|:----:|:----:|:----:|:----:|:----:|"]
    IMEICode = os.environ['IMEICODE']
    aipaoer = Aipaoer(IMEICode)
    if aipaoer.check_imeicode():
        aipaoer.get_info()
        aipaoer.get_runId()
        fin = aipaoer.upload_record()
        if(fin.get('msg') == 'success'):
            ends.append(fin.get('end'))
            text = "跑步结果-成功"
        else:
            ends.append('|'+names[index]+'|error||||')
            text = "跑步结果-失败"
    else:
        ends = ["IMEICode失效"]
        text = "跑步结果-失败"
    desp = "\r\n".join(ends)  # 将跑步详细结果转为字符串
    print(desp)

    body = {
        "text": text,
        "desp": desp
    }
    if(weixin_send(os.environ['SCKEY'], body)):
        print("微信推送成功")
    else:
        print("微信推送失败")


if __name__ == "__main__":
    main()