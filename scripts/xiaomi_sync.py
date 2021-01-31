import requests,time,re,json,random
import base64
from pprint import pprint

now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; MI 6 MIUI/20.6.18)'
        }
 
def get_code(location):
    code_pattern = re.compile("(?<=access=).*?(?=&)")
    code = code_pattern.findall(location)[0]
    return code
 
def login(user,password):
    url1 = "https://api-user.huami.com/registrations/+86" + user + "/tokens"
    headers = {
        "Content-Type":"application/x-www-form-urlencoded;charset=UTF-8",
    "User-Agent":"MiFit/4.6.0 (iPhone; iOS 14.0.1; Scale/2.00)"
        }
    data1 = {
        "client_id":"HuaMi",
        "password":f"{password}",
        "redirect_uri":"https://s3-us-west-2.amazonaws.com/hm-registration/successsignin.html",
        "token":"access"
        }
    r1 = requests.post(url1,data=data1,headers=headers,allow_redirects=False)
    location = r1.headers["Location"]
    try:
        code = get_code(location)
    except:
        return 0,0
     
    url2 = "https://account.huami.com/v2/client/login"
    data2 = {
        "app_name":"com.xiaomi.hm.health",
        "app_version":"4.6.0",
        "code":f"{code}",
        "country_code":"CN",
        "device_id":"2C8B4939-0CCD-4E94-8CBA-CB8EA6E613A1",
        "device_model":"phone",
        "grant_type":"access_token",
        "third_name":"huami_phone",
        } 
    r2 = requests.post(url2,data=data2,headers=headers).json()
    login_token = r2["token_info"]["login_token"]
    userid = r2["token_info"]["user_id"]
 
    return login_token,userid

def get_time():
    url = 'http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp'
    response = requests.get(url,headers=headers).json()
    t = response['data']['t']
    return t
  
def get_app_token(login_token):
    url = f"https://account-cn.huami.com/v1/client/app_tokens?app_name=com.xiaomi.hm.health&dn=api-user.huami.com%2Capi-mifit.huami.com%2Capp-analytics.huami.com&login_token={login_token}"
    response = requests.get(url,headers=headers).json()
    app_token = response['token_info']['app_token']
    return app_token


def get_band_data(app_token, user_id):
    t = get_time()
    band_data_url='https://api-mifit-cn.huami.com/v1/data/band_data.json'
    device_data_url = 'https://api-mifit-cn.huami.com/users/1011920265/devices'
    weight_url = "https://api-mifit-cn2.huami.com/users/1011920265/members/1591191251801/weightRecords"
    headers={
		'apptoken': app_token,
	}
    data={
        't': t,
		'query_type': 'summary',
		'device_type': 0,
		'userid': user_id,
		'from_date': '2019-01-01',
		'to_date': '2019-12-31',
	}
    r = requests.get(band_data_url,params=data,headers=headers)
    data = r.json()
    print(list(data.keys()))
    print(len(data["data"]))
    # day_data = data["data"][30]
    # summary=json.loads(base64.b64decode(day_data['summary']))
    print(requests.get(device_data_url, headers=headers).json())
    r = requests.get(weight_url, headers=headers)
    print(r.json())
 
def main(user_name, password):
    login_token, userid = login(user_name,password)
    print(login_token, userid)
    app_token = get_app_token(login_token)
    get_band_data(app_token, userid)


if __name__ == "__main__":
    main("a", "v")
