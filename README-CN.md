![running_page](https://socialify.git.ci/yihong0618/running_page/image?description=1&font=Inter&forks=1&issues=1&language=1&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fshaonianche%2Fgallery%2Fmaster%2Frunning_page%2Frunning_page_logo_150*150.jpg&owner=1&pulls=1&stargazers=1&theme=Light)

# [这里是白银越野赛全部 21 位逝者的故事](https://github.com/yihong0618/running_page/issues/135)

R.I.P. 希望大家都能健康顺利的跑过终点，逝者安息。

# [打造个人跑步主页](https://yihong.run/running)

[English](README.md) | 简体中文 | [Wiki](https://wiki.mfydev.run/)

<details>
<summary>GIF 展示</summary>

![running_page](https://user-images.githubusercontent.com/15976103/98808834-c02f1d80-2457-11eb-9a7c-70e91faa5e30.gif)

</details>

## [大家的跑步主页展示](https://github.com/yihong0618/running_page/issues/12)

| Runner                                          | page                                       | App       |
| ----------------------------------------------- | ------------------------------------------ | --------- |
| [shaonianche](https://github.com/shaonianche)   | https://run.duangfei.org                   | Nike      |
| [yihong0618](https://github.com/yihong0618)     | https://yihong.run/running                 | Nike      |
| [superleeyom](https://github.com/superleeyom)   | https://running.leeyom.top                 | Nike      |
| [geekplux](https://github.com/geekplux)         | https://activities.geekplux.com            | Nike      |
| [guanlan](https://github.com/guanlan)           | https://grun.vercel.app                    | Strava    |
| [tuzimoe](https://github.com/tuzimoe)           | https://run.tuzi.moe                       | Nike      |
| [ben_29](https://github.com/ben-29)             | https://running.ben29.xyz                  | Strava    |
| [kcllf](https://github.com/kcllf)               | https://running-tau.vercel.app             | Garmin-cn |
| [mq](https://github.com/MQ-0707)                | https://running-iota.vercel.app            | Keep      |
| [zhaohongxuan](https://github.com/zhaohongxuan) | https://running-page-psi.vercel.app        | Keep      |
| [yvetterowe](https://github.com/yvetterowe)     | https://run.haoluo.io                      | Strava    |
| [love-exercise](https://github.com/KaiOrange)   | https://run.kai666666.top                  | Keep      |
| [zstone12](https://github.com/zstone12)         | https://running-page.zstone12.vercel.app   | Keep      |
| [Lax](https://github.com/Lax)                   | https://lax.github.io/running              | Keep      |
| [lusuzi](https://github.com/lusuzi)             | https://running.lusuzi.vercel.app          | Nike      |
| [wh1994](https://github.com/wh1994)             | https://run4life.fun                       | Garmin    |
| [liuyihui](https://github.com/YiHui-Liu)        | https://run.foolishfox.cn                  | Keep      |
| [FrankSun](https://github.com/hi-franksun)      | https://hi-franksun.github.io/running_page | Nike      |
| [AhianZhang](https://github.com/AhianZhang)     | https://running.ahianzhang.com             | Keep      |
| [L1cardo](https://github.com/L1cardo)           | https://run.licardo.cn                     | Nike      |
| [luckylele666](https://github.com/luckylele666) | https://0000928.xyz                        | Strava    |
| [MFYDev](https://github.com/MFYDev)             | https://mfydev.run                         | Garmin-cn |
| [Jim Gao](https://github.com/tianheg)             | https://run.yidajiabei.xyz/ | Keep |
| [Oysmart](https://github.com/oysmart)             | https://run.ouyang.wang                  | Garmin-cn |
| [Eished](https://github.com/eished)             | https://run.iknow.fun                      | Keep      |
| [Liuxin](https://github.com/liuxindtc)             | https://liuxin.run                   |  Nike      |

## 它是怎么工作的

![image](https://user-images.githubusercontent.com/15976103/105784027-e1ad9900-5fb2-11eb-9479-372be21482f1.png)

## 特性

1. GitHub Actions 管理自动同步跑步进程及自动生成新的页面
2. Gatsby 生成的静态网页，速度快
3. 支持 Vercel(推荐) 和 GitHub Pages 自动部署
4. React Hooks
5. Mapbox 进行地图展示
6. Nike 及 Runtastic(Adidas Run) 以及佳明（佳明中国）及 Keep 等, 自动备份 gpx 数据，方便备份及上传到其它软件

> 因为数据存在 gpx 和 data.db 中，理论上支持几个软件一起，你可以把之前各类 app 的数据都同步到这里（建议本地同步，之后 actions 选择正在用的 app）

> 注: 如果你不想公开数据，可以选择 strava 的模糊处理，或 private 仓库。

<details>
<summary>缩放地图彩蛋</summary>

![image](https://user-images.githubusercontent.com/15976103/95644909-a31bcd80-0aec-11eb-9270-869b0a94f59f.png)

</details>

## 支持

- **[Strava](#strava)**
- **[Nike Run Club](#nike-run-club)**
- **[Garmin](#Garmin)**
- **[Garmin-cn](#garmin-cn-大陆用户请用这个)**
- **[Keep](#Keep)**
- **[悦跑圈](#joyrun悦跑圈)** (因悦跑圈限制单个设备原因，无法自动化)
- **[咕咚](#codoon咕咚)** (因咕咚限制单个设备原因，无法自动化)
- **[GPX](#GPX)**
- **[Nike+Strava(Using NRC Run, Strava backup data)](#nikestrava)**
- **[Strava_to_Garmin(Using Strava Run, Garmin backup data)](#)**

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

## 替换 `src/utils/const.js` 文件中的 Mapbox token

> 建议有能力的同学把代码中的 Mapbox token 自己的 [Mapbox token](https://www.mapbox.com/)

```javascript
const MAPBOX_TOKEN =
  'pk.eyJ1IjoieWlob25nMDYxOCIsImEiOiJja2J3M28xbG4wYzl0MzJxZm0ya2Fua2p2In0.PNKfkeQwYuyGOTT_x9BJ4Q';
```

### 如果你是海外用户请更改 `IS_CHINESE = false` in `src/utils/const.js`

## 一些个性化选项

在仓库目录下找到 `gatsby-config.js`，找到以下内容并修改成你自己想要的。

```javascript
siteMetadata: {
  siteTitle: 'Running Page', #网站标题
  siteUrl: 'https://yihong.run', #网站域名
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU', #左上角LOGO
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog', #右上角导航名称
      url: 'https://yihong.run/running', #右上角导航链接
    },
    {
      name: 'About',
      url: 'https://github.com/yihong0618/running_page/blob/master/README-CN.md',
    },
  ],
},
```

## 下载您的 Nike Run Club/Strava/Garmin/Garmin-cn/Keep 数据, [别忘了在 `total` 页面生成可视化 SVG](#Total-Data-Analysis).

### GPX

<details>
<summary>Make your <code>GPX</code> data</summary>
<br>

把其它软件生成的 gpx files 拷贝到 GPX_OUT 之后运行

```python
python3(python) scripts/gpx_sync.py
```

</details>

### Keep

<details>
<summary>获取您的 Keep 数据</summary>

确保自己的账号能用手机号 + 密码登陆 (不要忘记添加 secret 和更改自己的账号，在 GitHub Actions 中), 注: 海外手机号需要换成国内 +86 的手机号

```python
python3(python) scripts/keep_sync.py ${your mobile} ${your password}
```

示例：

```python
python3(python) scripts/keep_sync.py 13333xxxx example
```

> 注：我增加了 keep 可以导出 gpx 功能（因 keep 的原因，距离和速度会有一定缺失）, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) scripts/keep_sync.py ${your mobile} ${your password} --with-gpx
```

示例：

```python
python3(python) scripts/keep_sync.py 13333xxxx example --with-gpx
```

</details>

### JoyRun（悦跑圈）

<details>
<summary>获取您的悦跑圈数据</summary>

获取登陆验证码：

确保自己的账号能用手机号 + 验证码登陆

点击获取验证码, 注： **不要在手机输入验证码，拿到验证码就好，用这个验证码放到下方命令中**

![image](https://user-images.githubusercontent.com/15976103/102352588-e3af3000-3fe2-11eb-8131-14946b0262eb.png)

```python
python3(python) scripts/joyrun_sync.py ${your mobile} ${your 验证码}
```

示例：

```python
python3(python) scripts/joyrun_sync.py 13333xxxx xxxx
```

> 注：我增加了 joyrun 可以导出 gpx 功能, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) scripts/joyrun_sync.py ${your mobile} ${your 验证码} --with-gpx
```

示例：

```python
python3(python) scripts/joyrun_sync.py 13333xxxx example --with-gpx
```

> 注：因为验证码有过期时间，我增加了 cookie uid sid 登陆的方式， uid 及 sid 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/15976103/102354069-05a9b200-3fe5-11eb-9b30-221c32bbc607.png)

示例：

```python
python3(python) scripts/joyrun_sync.py 1393xx30xxxx 97e5fe4997d20f9b1007xxxxx --from-uid-sid --with-gpx
```

</details>

### Codoon（咕咚）

<details>
<summary>获取您的咕咚数据</summary>

```python
python3(python) scripts/codoon_sync.py ${your mobile or email} ${your password}
```

示例：

```python
python3(python) scripts/codoon_sync.py 13333xxxx xxxx
```

> 注：我增加了 Codoon 可以导出 gpx 功能, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) scripts/codoon_sync.py ${your mobile or email} ${your password} --with-gpx
```

示例：

```python
python3(python) scripts/codoon_sync.py 13333xxxx xxxx --with-gpx
```

> 注：因为登录 token 有过期时间限制，我增加了 refresh_token&user_id 登陆的方式， refresh_token 及 user_id 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/6956444/105690972-9efaab00-5f37-11eb-905c-65a198ad2300.png)

示例：

```python
python3(python) scripts/codoon_sync.py 54bxxxxxxx fefxxxxx-xxxx-xxxx --from-auth-token
```

</details>

### Garmin

<details>
<summary>获取您的 Garmin 数据</summary>

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password}
```

示例：

```python
python3(python) scripts/garmin_sync.py example@gmail.com example
```

</details>

### Garmin-CN (大陆用户请用这个)

<details>
<summary>获取您的 Garmin-CN 数据</summary>
如果你只想同步跑步数据请增加 --only-run

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password} --is-cn
```

示例：

```python
python3(python) scripts/garmin_sync.py example@gmail.com example --is-cn
```

</details>

### Nike Run Club

<details>
<summary>获取 Nike Run Club 数据</summary>

**请注意：当您选择将 running_page 部署在自己的服务器上时，由于 Nike 已经封禁了一部分 IDC 的服务器 IP 段，您的服务器可能不能正常同步 Nike Run Club 的数据并显示 `403 error` ，这时您将不得不选择其他的托管方式。**

获取 Nike 的 refresh_token

1. 登录 [Nike](https://www.nike.com) 官网
2. In Developer -> Application-> Storage -> https:unite.nike.com 中找到 refresh_token

![image](https://user-images.githubusercontent.com/15976103/94448123-23812b00-01dd-11eb-8143-4b0839c31d90.png) 3. 在项目根目录下执行:

```python
python3(python) scripts/nike_sync.py ${nike refresh_token}
```

示例：

```python
python3(python) scripts/nike_sync.py eyJhbGciThiMTItNGIw******
```

![example img](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/nike_sync_%20example.png)

</details>

### Strava

<details>
<summary>获取 Strava 数据</summary>

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

![get_all_permissions](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_all_permissions.png) 5. 提取授权后返回链接中的 code 值  
例如：

```
http://localhost/exchange_token?state=&code=1dab37edd9970971fb502c9efdd087f4f3471e6e&scope=read,activity:write,activity:read_all,profile:write,profile:read_all,read_all
```

`code` 数值为：

```
1dab37edd9970971fb502c9efdd087f4f3471e6
```

![get_code](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_code.png) 6. 使用 Client_id、Client_secret、Code 请求 refresch_token  
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

</details>

### Nike+Strava

<details>
<summary>Get your <code>Nike Run Club</code> data and upload to strava</summary>

<br>

1. 完成 nike 和 strava 的步骤
2. 在项目根目录下执行::

```python
python3(python) scripts/nike_to_strava_sync.py ${nike_refresh_token} ${client_id} ${client_secret} ${strava_refresch_token}
```

示例：

```python
python3(python) scripts/nike_to_strava_sync.py eyJhbGciThiMTItNGIw******  xxx xxx xxx
```

</details>

### Total Data Analysis

<details>
<summary>生成数据展示</summary>

- 生成数据展示 SVG
- 展示效果：[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/master/assets/github.svg)、[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/28fa801e4e30f30af5ae3dc906bf085daa137936/assets/grid.svg)

> 注: 感兴趣的同学可以改下方参数 (--special-distance 10 --special-distance2 20, 10km~20km 展示为 special-color1 20km 以上展示为 special-color2, --min-distance 10.0 用来筛选 10km 以上的)

```
python3(python) scripts/gen_svg.py --from-db --title "${{ env.TITLE }}" --type github --athlete "${{ env.ATHLETE }}" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
```

```
python3(python) scripts/gen_svg.py --from-db --title "${{ env.TITLE_GRID }}" --type grid --athlete "${{ env.ATHLETE }}"  --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
```

生成年度环形数据

```
python3(python) scripts/gen_svg.py --from-db --type circular --use-localtime
```

更多展示效果参见：  
https://github.com/flopp/GpxTrackPoster

</details>

## server(recommend vercel)

<details>
<summary>使用 Vercel 部署</summary>

1. vercel 连接你的 GitHub repo

![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)

2. import repo

![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)

2. 等待部署完毕
3. 访问
</details>

<details>
<summary> 使用 Cloudflare 部署 </summary>
<br>

1. 在 `Pages` 中点击 `Create a project` 以连接到你的仓库

2. 点击 `Begin setup` 后，修改项目的 `Build settings`。

3. 在 `Framework preset` 中选择 `Gatsby` 框架。

4. 向下滚动，点击 `Environment variables` 修改变量如下：

   > Variable name = `PYTHON_VERSION`, Value = `3.7`

5. 点击 `Save and Deploy`，完成部署。

</details>

<details>
<summary> 部署到 GitHub Pages </summary>

1. 配置 GitHub Action。如需使用自定义域名，可以修改 [.github/workflows/gh-pages.yml](.github/workflows/gh-pages.yml) 中的 `fqdn`（默认已注释掉）

2. 修改 `gatsby-config.js`，更新 `pathPrefix`。【如果使用自定义域名，可跳过这一步】

3. 在项目的 `Actions -> Workflows -> All Workflows` 中选择 Publish GitHub Pages，点击 `Run workflow`

4. 在项目的 `Settings -> GitHub Pages -> Source` 部分，选择 `Branch: gh-pages` 并点击 `Save`。
</details>

## GitHub Actions (Fork 的同学请一定不要忘了把 GitHub Token 改成自己的，否则会 push 到我的 repo 中，谢谢大家。)

<details>
<summary>修改 GitHub Actions Token</summary>

Actions [源码](https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
需要做如下步骤

1. 更改成你的 app type 及 info
   ![image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)
2. 在 repo Settings > Secrets 中增加你的 secret (只添加你需要的即可)
   ![image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)
   我的 secret 如下
   ![image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png)
3. 添加你的 [GitHub secret](https://github.com/settings/tokens)并和项目中的 GitHub secret 同名
   ![image](https://user-images.githubusercontent.com/15976103/94450721-2f222100-01e0-11eb-94a7-ef1f06fc0a59.png)

</details>

# TODO

- [x] 完善这个文档
- [x] 支持佳明，佳明中国
- [x] 支持 keep
- [ ] 支持苹果自带运动
- [x] 支持 nike + strava
- [x] 支持咕咚
- [ ] 尝试支持小米运动
- [x] 支持英语
- [x] 完善代码
- [x] 清理整个项目
- [x] 完善前端代码
- [x] better actions
- [ ] tests
- [ ] 支持不同的运动类型

# 参与项目

- 任何 Issues PR 均欢迎。
- 可以提交 PR share 自己的 Running page 在 README 中。

提交 PR 前:

- 使用 black 对 Python 代码进行格式化。(black .)
- 使用 isort 对 Python import 进行格式化。(isort --profile black  **/**/*.py)

# 特别感谢

- @[flopp](https://github.com/flopp) 特别棒的项目 [GpxTrackPoster](https://github.com/flopp/GpxTrackPoster)
- @[danpalmer](https://github.com/danpalmer) 原始的 UI 设计
- @[shaonianche](https://github.com/shaonianche) icon 设计及文档
- @[geekplux](https://github.com/geekplux) 帮助及鼓励, 重构了前端代码，学到了不少
- @[ben-29](https://github.com/ben-29) 搞定了咕咚，和我一起搞定了悦跑圈，太厉害了
- @[MFYDev](https://github.com/MFYDev) Wiki

# 赞赏

谢谢就够了
