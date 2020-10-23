# [打造个人跑步主页](https://yihong.run/running) 
简体中文 | [English](https://github.com/yihong0618/running_page/blob/master/README-EN.md)

## 特性

1. GitHub Actions 管理自动同步跑步进程及自动生成新的页面
2. Gatsby 生成的静态网页，速度快
3. 支持 Vercel(推荐) 自动部署
4. React Hooks
5. Mapbox 进行地图展示
6. Nike 及 Runtastic(Adidas Run) 以及佳明（佳明中国）自动备份 gpx 数据，方便备份及上传到其它软件

## 支持
- Strava
- Nike Run Club
- Runtastic(Adidas Run)
- Garmin
- Garmin-cn
- Keep

## 下载
```
git clone https://github.com/yihong0618/running_page.git
```

## 安装及测试
    ```
    pip3 install -r requirements.txt
    yarn install
    yarn develop
    ```
访问 http://localhost:8000/ 查看


## 本地数据同步
删除项目中的测试数据，在根目录下执行
```bash
rm scripts/data.db GPX_OUT/* activities/*
```
或者
```bash
rm scripts/data.db
rm GPX_OUT/*
rm activities/*
```
## 下载您的 Runtastic(Adidas Run)/Nike Run Club/Strava/Garmin/Garmin-cn/Keep 数据

### Keep

确保自己的账号能用手机号 + 密码登陆 (不要忘记添加secret和更改自己的账号，在 GitHub Actions中)
```python
python3(python) scripts/keep_sync.py ${your mobile} ${your password}
```
示例：
```python
python3(python) scripts/keep_sync.py 13333xxxx example
```
注：我增加了 keep 可以导出 gpx 功能（因 keep 的原因，距离和速度会有一定缺失）, 执行如下命令，导出的 gpx会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) scripts/keep_sync.py ${your mobile} ${your password} --with-gpx
```
示例：
```python
python3(python) scripts/keep_sync.py 13333xxxx example --with-gpx
```

### Garmin

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password}
```
示例：
```python
python3(python) scripts/garmin_sync.py example@gmail.com example
```

### Garmin-CN(大陆用户请用这个)

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password} --is-cn
```
示例：
```python
python3(python) scripts/garmin_sync.py example@gmail.com example --is-cn
```

### Runtastic(Adidas Run)

```python
python3(python) scripts/runtastic_sync.py ${your email} ${your password}
```
示例：
```python
python3(python) scripts/runtastic_sync.py example@gmail.com example
```

### Nike Run Club

获取 Nike 的 refresh_token
1. 登录 [Nike](https://www.nike.com) 官网
2. In Developer -> Application-> Storage -> https:unite.nike.com 中找到 refresh_token

    ![image](https://user-images.githubusercontent.com/15976103/94448123-23812b00-01dd-11eb-8143-4b0839c31d90.png)
3. 在项目根目录下执行:

    ```python
    python3(python) scripts/nike_sync.py ${nike refresh_token}
    ```
    示例：
    ```python
    python3(python) scripts/nike_sync.py eyJhbGciThiMTItNGIw******
    ```
    ![example img](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/nike_sync_%20example.png)


### Strava

1. 注册/登陆 [Strava](https://www.strava.com/) 账号
2. 登陆成功后打开 [Strava Developers](http://developers.strava.com) -> [Create & Manage Your App](https://strava.com/settings/api)

3. 创建 `My API Application`   
    输入下列信息：
    ![My API Application](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/strava_settings_api.png)
    创建成功：
    ![](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/created_successfully_1.png)
4. 使用以下链接请求所有权限   
将 ${your_id} 替换为 My API Application 中的 Client ID 后访问完整链接
    ```
    https://www.strava.com/oauth/authorize?client_id=${your_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all,profile:write,activity:write
    ```
    ![get_all_permissions](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_all_permissions.png)
5. 提取授权后返回链接中的 code 值   
    例如：
    ```
    http://localhost/exchange_token?state=&code=1dab37edd9970971fb502c9efdd087f4f3471e6e&scope=read,activity:write,activity:read_all,profile:write,profile:read_all,read_all
    ```
    `code` 数值为：
    ```
    1dab37edd9970971fb502c9efdd087f4f3471e6
    ```
    ![get_code](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_code.png)
6. 使用 Client_id、Client_secret、Code 请求 refresch_token   
    在 `终端/iTerm` 中执行：
    ```
    curl -X POST https://www.strava.com/oauth/token \
    -F client_id=${Your Client ID} \
    -F client_secret=${Your Client Secret} \
    -F code=${Your Code} \
    -F grant_type=authorization_code
    ```
    示例：
    ```
    curl -X POST https://www.strava.com/oauth/token \
    -F client_id=12345 \
    -F client_secret=b21******d0bfb377998ed1ac3b0 \
    -F code=d09******b58abface48003 \
    -F grant_type=authorization_code
    ```
    ![get_refresch_token](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_refresch_token.png)

7. 同步数据至 Strava   
在项目根目录执行：
    ```python
    python3(python) scripts/strava_sync.py ${client_id} ${client_secret} ${refresch_token}
    ```
    其他资料参见
    https://developers.strava.com/docs/getting-started   
    https://github.com/barrald/strava-uploader   
    https://github.com/strava/go.strava

### Total Data Analysis

- 生成数据展示 SVG
- 展示效果：[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/master/assets/github.svg)、[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/28fa801e4e30f30af5ae3dc906bf085daa137936/assets/grid.svg)

    ```
    python3(python) scripts/gen_svg.py --from-db --title "${{ env.TITLE }}" --type github --athlete "${{ env.ATHLETE }}" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
    ```

    ```
    python3(python) scripts/gen_svg.py --from-db --title "${{ env.TITLE_GRID }}" --type grid --athlete "${{ env.ATHLETE }}"  --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
    ```
    更多展示效果参见：   
    https://github.com/flopp/GpxTrackPoster

## server(recommend vercel)
1. vercel 连接你的 GitHub repo
    ![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)
2. import repo
    ![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)
2. 等待部署完毕
3. 访问

## GitHub Actions 
Actions [源码](https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
需要做如下步骤
1. 更改成你的app type 及info
    ![image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)
2. 在repo Settings > Secrets 中增加你的secret(只添加你需要的即可)
    ![image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)
我的secret如下
    ![image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png)
3. 添加你的[GitHub secret](https://github.com/settings/tokens)并和项目中的 GitHub secret同名
    ![image](https://user-images.githubusercontent.com/15976103/94450721-2f222100-01e0-11eb-94a7-ef1f06fc0a59.png)

## 我的展示
![image](https://user-images.githubusercontent.com/15976103/87566339-775b9800-c6f5-11ea-803f-6c2f69801ee4.png)

# TODO

- [x] 完善这个文档
- [x] 支持佳明，佳明中国
- [x] 支持 keep
- [ ] 支持悦跑圈
- [ ] 支持 nike+strava, runtastic+strava
- [ ] 尝试支持咕咚，小米运动
- [ ] 支持英语
- [ ] 完善代码
- [ ] 添加新功能
- [ ] i18n

# 特别感谢

@[flopp](https://github.com/flopp)
