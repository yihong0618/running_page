# [打造个人跑步主页](https://yihong.run/running)

## 特性

1. GitHub Actions 管理自动同步跑步进程及自动生成新的页面
2. Gatsby 生成的静态网页，速度快
3. 支持Vercel(推荐) 自动部署
4. React Hooks
5. Mapbox 进行地图展示
6. Nike 及 Runtastic(Adidas Run)自动备份 gpx 数据，方便备份及上传到其它软件

## 支持

- Strava
- Nike Run Club
- Runtastic(Adidas Run)

## 下载
clone或fork这个repo

## 安装及测试

- pip3 install -r requirements.txt
- yarn install
- yarn develop

## 本地同步数据

### 删除我的测试数据

- rm scripts/data.db
- rm GPX_OUT/*
- rm activities/*

### Runtastic(Adidas Run)
```python
python3(python) scripts/runtastic_sync.py ${your email} ${your password}
```
### Nike Run Club
```python
python3(python) scripts/nike_sync.py ${nike refresh_token}
```
如何拿到nike refresh token
1. 登陆nike网站
2. 在开发者 -> Application-> Storage -> https:unite.nike.com 中找到refresh_token
![image](https://user-images.githubusercontent.com/15976103/94448123-23812b00-01dd-11eb-8143-4b0839c31d90.png)

### Strava
```python
python3(python) scripts/strava_sync.py ${client_id} ${client_id} ${refresch_token}
```
 如何获取到 client_id，client_id，refresch_token 见https://developers.strava.com/docs/getting-started/
 或参考下面项目
 1. https://github.com/barrald/strava-uploader
 2. https://github.com/strava/go.strava
 
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

## TODO

- [ ] 完善这个文档
- [ ] 支持佳明，佳明中国
- [ ] 支持悦跑圈
- [ ] 支持 nike+strava, runtastic+strava
- [ ] 支持英语
- [ ] 完善代码
- [ ] 添加新功能

## 特别感谢

@[floop](https://github.com/flopp)
