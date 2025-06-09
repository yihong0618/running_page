## Note

1. clone or Fork before vercel 404 need to pull the latest code
2. python in README means python3 python
3. use v2.0 need change vercel setting from gatsby to vite
4. 2023.09.26 garmin need secret_string(and in Actions) get

   ```bash
     python run_page/get_garmin_secret.py ${email} ${password}
     # if cn
     python run_page/get_garmin_secret.py ${email} ${password} --is-cn
   ```

5. 2024.09.29: Added `Elevation Gain` field, If you forked the project before this update, please run the following command:

   - To resolve errors: `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: activities.elevation_gain`
   - If you don't have a local environment, set `RUN_TYPE` to `db_updater` in the `.github/workflows/run_data_sync.yml` file once then change back.

   ```bash
     python run_page/db_updater.py
   ```

   - For old data: To include `Elevation Gain` for past activities, perform a full reimport.
   - To show the 'Elevation Gain' column, modify `SHOW_ELEVATION_GAIN` in `src/utils/const.ts`
   - note: `Elevation Gain` may be inaccurate. You can use Strava's "Correct Elevation" or Garmin's "Elev Corrections" feature for more precise data.

![running_page](https://socialify.git.ci/yihong0618/running_page/image?description=1&font=Inter&forks=1&issues=1&language=1&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fshaonianche%2Fgallery%2Fmaster%2Frunning_page%2Frunning_page_logo_150*150.jpg&owner=1&pulls=1&stargazers=1&theme=Light)

# [这里是白银越野赛全部 21 位逝者的故事](https://github.com/yihong0618/running_page/issues/135)

R.I.P. 希望大家都能健康顺利的跑过终点，逝者安息。

# [打造个人跑步主页](https://yihong.run/running)

[English](README.md) | 简体中文 | [Wiki](https://wiki.mfydev.run/)

<details>
<summary>GIF 展示</summary>

<br>

![running_page](https://user-images.githubusercontent.com/15976103/98808834-c02f1d80-2457-11eb-9a7c-70e91faa5e30.gif)

</details>

## [大家的跑步主页展示](https://github.com/yihong0618/running_page/issues/12)

<details>
<summary>Running page runners</summary>

<br>

| Runner                                            | page                                           | App         |
| ------------------------------------------------- | ---------------------------------------------- | ----------- |
| [zhubao315](https://github.com/zhubao315)         | <https://zhubao315.github.io/running>          | Strava      |
| [shaonianche](https://github.com/shaonianche)     | <https://run.duanfei.org>                      | Strava      |
| [yihong0618](https://github.com/yihong0618)       | <https://yihong.run>                           | Nike        |
| [superleeyom](https://github.com/superleeyom)     | <https://running.leeyom.top>                   | Strava      |
| [geekplux](https://github.com/geekplux)           | <https://activities.geekplux.com>              | Nike        |
| [guanlan](https://github.com/guanlan)             | <https://grun.vercel.app>                      | Strava      |
| [tuzimoe](https://github.com/tuzimoe)             | <https://run.tuzi.moe>                         | Nike        |
| [ben_29](https://github.com/ben-29)               | <https://running.ben29.xyz>                    | Strava      |
| [kcllf](https://github.com/kcllf)                 | <https://running-tau.vercel.app>               | Garmin-cn   |
| [mq](https://github.com/MQ-0707)                  | <https://running-iota.vercel.app>              | Keep        |
| [zhaohongxuan](https://github.com/zhaohongxuan)   | <https://zhaohongxuan.github.io/workouts>      | Strava      |
| [yvetterowe](https://github.com/yvetterowe)       | <https://run.haoluo.io>                        | Strava      |
| [love-exercise](https://github.com/KaiOrange)     | <https://run.kai666666.top>                    | Keep        |
| [zstone12](https://github.com/zstone12)           | <https://running-page.zstone12.vercel.app>     | Keep        |
| [Lax](https://github.com/Lax)                     | <https://lax.github.io/running>                | Keep        |
| [lusuzi](https://github.com/lusuzi)               | <https://running.lusuzi.vercel.app>            | Nike        |
| [wh1994](https://github.com/wh1994)               | <https://run4life.fun>                         | Garmin      |
| [liuyihui](https://github.com/YiHui-Liu)          | <https://run.foolishfox.cn>                    | Keep        |
| [sunyunxian](https://github.com/sunyunxian)       | <https://sunyunxian.github.io/running_page>    | Strava      |
| [AhianZhang](https://github.com/AhianZhang)       | <https://running.ahianzhang.com>               | Nike        |
| [L1cardo](https://github.com/L1cardo)             | <https://run.licardo.cn>                       | Nike        |
| [luckylele666](https://github.com/luckylele666)   | <https://0000928.xyz>                          | Strava      |
| [MFYDev](https://github.com/MFYDev)               | <https://mfydev.run>                           | Garmin-cn   |
| [Oysmart](https://github.com/oysmart)             | <https://run.ouyang.wang>                      | Garmin-cn   |
| [Eished](https://github.com/eished)               | <https://run.iknow.fun>                        | Keep        |
| [Liuxin](https://github.com/liuxindtc)            | <https://liuxin.run>                           | Nike        |
| [loucx](https://github.com/loucx)                 | <https://loucx.github.io/running>              | Nike        |
| [winf42](https://github.com/winf42)               | <https://winf42.github.io>                     | Garmin-cn   |
| [sun0225SUN](https://github.com/sun0225SUN)       | <https://run.sunguoqi.com>                     | Nike        |
| [Zhan](https://www.zlog.in/about)                 | <https://run.zlog.in>                          | Nike        |
| [Dennis](https://run.domon.cn)                    | <https://run.domon.cn>                         | Garmin-cn   |
| [hanpei](https://running.nexts.top)               | <https://running.nexts.top>                    | Garmin-cn   |
| [liugezhou](https://github.com/liugezhou)         | <https://run.liugezhou.online>                 | Strava      |
| [zhubao315](https://github.com/zhubao315)         | <https://zhubao315.github.io/running>          | Strava      |
| [Jason Tan](https://github.com/Jason-cqtan)       | <https://jason-cqtan.github.io/running_page>   | Nike        |
| [Conge](https://github.com/conge)                 | <https://conge.github.io/running_page>         | Strava      |
| [cvvz](https://github.com/cvvz)                   | <https://cvvz.github.io/running>               | Strava      |
| [zHElEARN](https://github.com/zHElEARN)           | <https://workouts.zhelearn.com>                | Strava      |
| [Rhfeng](https://sport.frh.life)                  | <https://sport.frh.life>                       | Garmin-cn   |
| [Ym9i](https://github.com/Ym9i)                   | <https://bobrun.vercel.app/>                   | Strava      |
| [jianchengwang](https://github.com/jianchengwang) | <https://jianchengwang.github.io/running_page> | Suunto      |
| [fxbin](https://github.com/fxbin)                 | <https://fxbin.github.io/sport-records/>       | Keep        |
| [shensl4499](https://github.com/shensl4499)       | <https://waner.run>                            | codoon      |
| [haowei93](https://github.com/haowei93)           | <https://running-fun.eu.org>                   | gpx         |
| [stevenash0822](https://github.com/stevenash0822) | <https://run.imangry.xyz/>                     | Strava      |
| [Vint](https://github.com/VintLin)                | <https://vinton.store/Running/>                | Keep        |
| [Muyids](https://github.com/muyids)               | <https://muyids.github.io/running>             | Garmin-cn   |
| [Gao Hao](https://github.com/efish2002)           | <https://efish2002.github.io/running_page/>    | Garmin-cn   |
| [Jinlei](https://github.com/iamjinlei0312)        | <https://jinlei.run/>                          | 咕咚        |
| [Ray Wang](https://github.com/raywangsy)          | <https://run.raywang.pro/>                     | Garmin      |
| [RealTiny656](https://github.com/tiny656)         | <https://tiny656.github.io/running_page/>      | JoyRun      |
| [EINDEX](https://github.com/eindex)               | <https://workouts.eindex.me/>                  | Strava/Nike |
| [Melt](https://github.com/fpGHwd)                 | <https://running.autove.dev/>                  | Strava      |
| [deepinwine](https://github.com/deepinwine)       | <https://deepin.autove.dev/>                   | Garmin-cn   |
| [Jeffggmm](https://github.com/Jeffggmm)           | <https://jeffggmm.github.io/workouts_page/>    | Garmin      |
| [s1smart](https://github.com/s1smart)             | <https://s1smart.github.io/running_page/>      | Strava      |
| [Ryan](https://github.com/85Ryan)                 | <https://85ryan.github.io/gooorun/>            | Strava      |
| [PPZ](https://github.com/8824PPZ)                 | <https://run.dudubbbbbbbbb.top/>               | Strava      |
| [Yer1k](https://github.com/Yer1k)                 | <https://running.yer1k.com/>                   | Strava      |
| [AlienVision](https://github.com/weaming)         | <https://run.drink.cafe/>                      | Strava      |
| [Vensent](https://github.com/Vensent)             | <https://vensent.github.io/workouts_page/>     | Garmin      |
| [Zeonsing](https://github.com/NoonieBao)          | <https://run.jogzeal.com/>                     | Coros       |
| [yaoper](https://github.com/yaoper)               | <https://running.yaoper.cn>                    | codoon      |
| [NoZTurn](https://github.com/NoZTurn)             | <https://run.jiangkai.org>                     | Strava      |
| [laqieer](https://github.com/laqieer)             | <https://laqieer.github.io/running_page/>      | Strava      |
| [Guoxin](https://github.com/guoxinl)              | <https://running.guoxin.space/>                | Strava      |
| [Darren](https://github.com/Flavored4179)         | <https://run.wdoc.top/>                        | tcx         |
| [Evan](https://github.com/LinghaoChan)            | <https://github.com/LinghaoChan/running>       | Keep        |
| [Shuqi](https://github.com/zhufengme)             | <https://runner-shuqi.devlink.cn/>             | Garmin      |
| [shugoal](https://github.com/shugoal)             | <https://shugoal.github.io/wk-shu/>            | Garmin      |

</details>

## 它是怎么工作的

![image](https://github.com/yihong0618/running_page/assets/15976103/85d8d59d-2639-431e-8406-9d818afbd4ab)

## 特性

1. GitHub Actions 自动同步跑步数据，生成展示页面
2. 支持 Vercel（推荐）和 GitHub Pages 自动部署
3. React Hooks
4. Mapbox 进行地图展示
5. Nike、Strava、佳明（佳明中国）及 Keep 等，自动备份 GPX 数据，方便备份及上传到其它软件

> 因为数据存在 gpx 和 data.db 中，理论上支持几个软件一起，你可以把之前各类 App 的数据都同步到这里（建议本地同步，之后 Actions 选择正在用的 App）
>
> 如果你不想公开数据，可以选择 `Strava` 的模糊处理，或 `private` 仓库。

<details>
<summary>缩放地图彩蛋</summary>

<br>

![image](https://user-images.githubusercontent.com/15976103/95644909-a31bcd80-0aec-11eb-9270-869b0a94f59f.png)

</details>

## 支持

- **[Strava](#strava)**
- **[New Way To Sync Nike Run Club](#nike-run-club-new)** ：NFC 同步的新方式
- **[Nike Run Club](#nike-run-club)**
- **[Garmin](#garmin)**
- **[Garmin-cn](#garmin-cn-大陆用户使用)**
- **[Keep](#keep)**
- **[悦跑圈](#joyrun悦跑圈)** ：限制单个设备，无法自动化
- **[咕咚](#codoon咕咚)** ：限制单个设备，无法自动化
- **[郁金香运动](#tulipsport)**
- **[GPX](#gpx)**
- **[TCX](#tcx)**
- **[FIT](#fit)**
- **[佳明国内同步国际](#garmin-cn-to-garmin)**
- **[Tcx+Strava(upload all tcx data to strava)](#tcx_to_strava)**
- **[Tcx+Garmin(upload all tcx data to Garmin)](#tcx_to_garmin)**
- **[Gpx+Strava(upload all gpx data to strava)](#gpx_to_strava)**
- **[Nike+Strava(Using NRC Run, Strava backup data)](#nikestrava)**
- **[Garmin_to_Strava(Using Garmin Run, Strava backup data)](#garmin_to_strava)**
- **[Strava_to_Garmin(Using Strava Run, Garmin backup data)](#strava_to_garmin)**
- **[Coros 高驰](#coros-高驰)**

## 视频教程

- <https://www.youtube.com/watch?v=reLiY9p8EJk>
- <https://www.youtube.com/watch?v=VdNkFxTX5QQ>

## 下载

```bash
git clone https://github.com/yihong0618/running_page.git --depth=1
```

## 安装及测试 (node >= 20 python >= 3.11)

```bash
pip3 install -r requirements.txt
npm install -g corepack && corepack enable && pnpm install
pnpm develop
```

访问 <http://localhost:5173/> 查看

## Docker

```bash
# NRC
docker build -t running_page:latest . --build-arg app=NRC --build-arg nike_refresh_token=""

# Garmin
docker build -t running_page:latest . --build-arg app=Garmin --build-arg secret_string=""

# Garmin-CN
docker build -t running_page:latest . --build-arg app=Garmin-CN --build-arg secret_string=""

# Strava
docker build -t running_page:latest . --build-arg app=Strava --build-arg client_id=""  --build-arg client_secret=""  --build-arg refresh_token=""

#Nike_to_Strava
docker build -t running_page:latest . --build-arg app=Nike_to_Strava  --build-arg nike_refresh_token="" --build-arg client_id=""  --build-arg client_secret=""  --build-arg refresh_token=""

# Keep
docker build -t running_page:latest . --build-arg app=Keep --build-arg keep_phone_number="" --build-arg keep_password=""

#启动
docker run -itd -p 80:80   running_page:latest

#访问
访问 ip:80 查看

```

## 替换 Mapbox token

> 建议有能力的同学把 `src/utils/const.ts` 文件中的 Mapbox token 自己的 [Mapbox token](https://www.mapbox.com/)
>
> 如果你是海外用户请更改 `IS_CHINESE = false` in `src/utils/const.ts`

```typescript
const MAPBOX_TOKEN =
  'pk.eyJ1IjoieWlob25nMDYxOCIsImEiOiJja2J3M28xbG4wYzl0MzJxZm0ya2Fua2p2In0.PNKfkeQwYuyGOTT_x9BJ4Q';
```

## 更改默认地图服务样式

> 在使用默认的地图服务样式之外，你可以通过修改 src/utils/const.ts 文件中的以下配置项来自定义地图显示。

```typescript
const MAP_TILE_VENDOR = 'maptiler';
const MAP_TILE_STYLE = 'winter-dark';
const MAP_TILE_ACCESS_TOKEN = '你的access token';
```

目前，支持的MAP_TILE_VENDOR选项包括：

- **"mapbox"** - Mapbox 地图服务

- **"maptiler"** - MapTiler地图服务

- **"stadiamaps"** - Stadia Maps地图服务

每个`MAP_TILE_VERNDOR`都提供了多种`MAP_TILE_STYLE`选择，配置时需保证匹配。具体的`MAP_TILE_STYLE`名称，可参考`src/utils/const.ts`文件中的定义。

当使用 **"maptiler"** 或是 **"stadiamaps"** 时，需配置`MAP_TILE_ACCESS_TOKEN`。默认的token在不更改的情况下，使用时会发生配额超限的问题。

- **MapTiler**: 在 https://cloud.maptiler.com/auth/widget 注册获取（免费）

- **Stadia Maps**: 在 https://client.stadiamaps.com/signup/ 注册获取（免费）

## 个性化设置

> 在仓库目录下找到 `src/static/site-metadata.ts`，找到以下内容并修改成你自己想要的。

```typescript
siteMetadata: {
  siteTitle: 'Running Page', #网站标题
  siteUrl: 'https://yihong.run', #网站域名
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU', #左上角 LOGO
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

> 修改 `src/utils/const.ts` 文件中的样式：

```typescript
// styling: 关闭虚线：设置为 `false`
const USE_DASH_LINE = true;
// styling: 透明度：[0, 1]
const LINE_OPACITY = 0.4;
// update for now 2024/11/17 the privacy mode is true
// styling: 开启隐私模式 (不显示地图仅显示轨迹): 设置为 `true`
// 注意：此配置仅影响页面显示，数据保护请参考下方的 "隐私保护"
const PRIVACY_MODE = false;
// styling: 默认关灯：设置为 `false`, 仅在隐私模式关闭时生效 (`PRIVACY_MODE` = false)
const LIGHTS_ON = true;
// styling: 是否显示列 ELEVATION_GAIN
const SHOW_ELEVATION_GAIN = false;
```

> 隐私保护：设置下面环境变量：

```bash
# 忽略每个 polyline 的起点和终点的长度（单位：米）。
IGNORE_START_END_RANGE = 200

# 忽略下面 polyline 中每个点的距离的圆圈（单位：米）。
IGNORE_RANGE = 200

# 包含要忽略的点的折线。
IGNORE_POLYLINE = ktjrFoemeU~IorGq}DeB

# 在保存到数据库之前进行过滤，你会丢失一些数据，但可以保护你的隐私，如果你使用的是公共仓库，建议设置为 1。不设置可关闭。
IGNORE_BEFORE_SAVING = 1
```

> 你可以使用`
Google Maps` 的 [互动式多段线编码器实用程序](https://developers.google.com/maps/documentation/utilities/polylineutility)，来制作你的 `IGNORE_POLYLINE`。如果你在中国，请使用卫星图制作，避免火星坐标漂移。

## 下载数据到本地

> 下载您的 Nike Run Club/Strava/Garmin/Garmin-cn/Keep 数据到本地，别忘了在 total 页面生成可视化 SVG

### GPX

<details>
<summary>Make your <code>GPX</code> data</summary>

<br>

把其它软件生成的 `gpx files` 拷贝到 `GPX_OUT` 之后运行

```bash
python run_page/gpx_sync.py
```

</details>

### TCX

<details>
<summary>Make your <code>TCX</code> data</summary>

<br>

把其它软件生成的 `tcx files` 拷贝到 `TCX_OUT` 之后运行

```bash
python run_page/tcx_sync.py
```

</details>

### FIT

<details>
<summary>Make your <code>FIT</code> data</summary>

<br>

把其它软件生成的 fit files 拷贝到 FIT_OUT 之后运行

```bash
python run_page/fit_sync.py
```

</details>

### Keep

<details>
<summary>获取您的 Keep 数据</summary>

<br>

> 确保自己的账号能用手机号 + 密码登陆 (不要忘记添加 secret 和更改自己的账号，在 GitHub Actions 中), 注：海外手机号需要换成国内 +86 的手机号

```bash
python run_page/keep_sync.py ${your mobile} ${your password}
```

示例：

```bash
python run_page/keep_sync.py 13333xxxx example
```

> 我增加了 keep 可以导出 gpx 功能（因 keep 的原因，距离和速度会有一定缺失）, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件。

```bash
python run_page/keep_sync.py ${your mobile} ${your password} --with-gpx
```

示例：

```bash
python run_page/keep_sync.py 13333xxxx example --with-gpx
```

> 增加了 keep 对其他运动类型的支持，目前可选的有 running, cycling, hiking，默认的运动数据类型为 running。

```bash
python run_page/keep_sync.py ${your mobile} ${your password} --with-gpx --sync-types running cycling hiking
```

示例：

```bash
python run_page/keep_sync.py 13333xxxx example --with-gpx --sync-types running cycling hiking
```

</details>

<details>
<summary>路线偏移修正</summary>

<br>

如果您得到的运动路线与实际路线对比有整体偏移，可以修改代码中的参数进行修正

> Keep 目前采用的是 GCJ-02 坐标系，因此导致得到运动数据在使用 WGS-84 坐标系的平台（Mapbox、佳明等）中显示轨迹整体偏移

- 修改 `run_page/keep_sync.py` 文件中的参数：

```python
# If your points need trans from gcj02 to wgs84 coordinate which use by Mapbox
TRANS_GCJ02_TO_WGS84 = True
```

</details>

### JoyRun（悦跑圈）

> 因悦跑圈限制单个设备，无法自动化。

<details>
<summary>获取您的悦跑圈数据</summary>

<br>

1. 获取登陆验证码：
2. 确保自己的账号能用手机号 + 验证码登陆
3. 点击获取验证码

> 不要在手机输入验证码，拿到验证码就好，用这个验证码放到下方命令中

![image](https://user-images.githubusercontent.com/15976103/102352588-e3af3000-3fe2-11eb-8131-14946b0262eb.png)

```bash
python run_page/joyrun_sync.py ${your mobile} ${your 验证码} --athlete ${your own name}
```

示例：

```bash
python run_page/joyrun_sync.py 13333xxxx xxxx --athlete yihong0618
```

joyrun 导出 gpx 文件

> 导出的 gpx 在 GPX_OUT 目录，方便上传到其它软件

```bash
python run_page/joyrun_sync.py ${your mobile} ${your 验证码} --with-gpx
```

示例：

```bash
python run_page/joyrun_sync.py 13333xxxx example --with-gpx
```

> 因为验证码有过期时间，我增加了 cookie uid sid 登陆的方式，uid 及 sid 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/15976103/102354069-05a9b200-3fe5-11eb-9b30-221c32bbc607.png)

示例：

```bash
python run_page/joyrun_sync.py 1393xx30xxxx 97e5fe4997d20f9b1007xxxxx --from-uid-sid --with-gpx
```

> 支持配置 min_grid_distance，默认为 10

```bash
python run_page/joyrun_sync.py 13333xxxx xxxx --athlete yihong0618 --min_grid_distance 5
```

</details>

### Codoon（咕咚）

> 因悦跑圈限制单个设备，无法自动化。

<details>
<summary>获取您的咕咚数据</summary>

<br>

```bash
python run_page/codoon_sync.py ${your mobile or email} ${your password}
```

示例：

```bash
python run_page/codoon_sync.py 13333xxxx xxxx
```

Codoon 导出 gpx

> 导出的 gpx 在 GPX_OUT 目录，方便上传到其它软件

```bash
python run_page/codoon_sync.py ${your mobile or email} ${your password} --with-gpx
```

示例：

```bash
python run_page/codoon_sync.py 13333xxxx xxxx --with-gpx
```

> 因为登录 token 有过期时间限制，我增加了 refresh_token&user_id 登陆的方式，refresh_token 及 user_id 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/6956444/105690972-9efaab00-5f37-11eb-905c-65a198ad2300.png)

示例：

```bash
python run_page/codoon_sync.py 54bxxxxxxx fefxxxxx-xxxx-xxxx --from-auth-token
```

</details>

<details>
<summary>路线偏移修正</summary>

<br>

如果您得到的运动路线与实际路线对比有整体偏移，可以修改代码中的参数进行修正

> 咕咚最初采用 GCJ-02 坐标系，在 2014 年 3 月份左右升级为 WGS-84 坐标系，导致升级之前的运动数据在使用 WGS-84 坐标系的平台（Mapbox、佳明等）中显示轨迹整体偏移

- 修改 `run_page/codoon_sync.py` 文件中的参数：

> TRANS_END_DATE 需要根据您的实际情况设定，程序会修正这一天之前的运动记录

```python
# If your points need trans from gcj02 to wgs84 coordinate which use by Mapbox
TRANS_GCJ02_TO_WGS84 = True
# trans the coordinate data until the TRANS_END_DATE, work with TRANS_GCJ02_TO_WGS84 = True
TRANS_END_DATE = "2014-03-24"
```

</details>

### TulipSport

<details>
<summary>获取您的郁金香运动数据</summary>

<br>

> 郁金香运动数据的获取方式采用开放平台授权模式，通过访问[RunningPage 授权页面](https://tulipsport.rdshoep.com)获取账号 TOKEN(不会过期，只能访问 2021 年之后的数据)，并在仓库的 GitHub Actions 环境配置中添加`TULIPSPORT_TOKEN`配置。

```bash
python run_page/tulipsport_sync.py ${tulipsport_token}
```

示例：

```bash
python run_page/tulipsport_sync.py nLgy****RyahI
```

</details>

### Garmin

<details>
<summary>获取您的 Garmin 数据</summary>

<br>

- 如果你只想同步跑步数据增加命令 --only-run

- 如果你想同步 `tcx` 格式，增加命令 --tcx

- 如果你想同步 `fit` 格式，增加命令 --fit

- 如果你使用 Garmin 作为数据源建议您将代码拉取到本地获取 Garmin 国际区的密钥，注意**Python 版本必须>=3.8**

#### 获取佳明国际区的密钥

在终端中输入以下命令

```bash
# 获取密钥
python run_page/get_garmin_secret.py ${your email} ${your password}
```

#### 执行佳明国际区同步脚本

复制上述终端中输出的密钥，如果您是使用 GitHub 请在 GitHub Action 中配置**GARMIN_SECRET_STRING**参数

示例：

```bash
python run_page/garmin_sync.py xxxxxxxxxxx
```

</details>

### Garmin-CN (大陆用户使用)

<details>
<summary>获取您的 Garmin CN 数据</summary>

<br>

- 如果你只想同步跑步数据请增加 --only-run
- 如果你想同步 `tcx` 格式，增加命令 --tcx
- 如果你想同步 `fit` 格式，增加命令 --fit
- 如果你使用 Garmin 作为数据源建议您将代码拉取到本地获取 Garmin 国际区的密钥，注意**Python 版本必须>=3.10**

#### 获取佳明 CN 的密钥

在终端中输入以下命令

```bash
# to get secret_string
python run_page/get_garmin_secret.py ${your email} ${your password} --is-cn
```

![get_garmin_cn_secret](docs/get_garmin_cn_secret.jpg)

#### 执行佳明国区同步脚本

复制上述终端中输出的密钥，如果您是使用 GitHub 请在 GitHub Action 中配置**GARMIN_SECRET_STRING_CN** 参数
![get_garmin_secret](docs/add_garmin_secret_cn_string.jpg)
示例：

```bash
python run_page/garmin_sync.py xxxxxxxxx --is-cn
```

仅同步跑步数据：

```bash
python run_page/garmin_sync.py xxxxxxxxxx --is-cn --only-run
```

</details>

### Garmin-CN to Garmin

<details>
<summary> 同步佳明 CN 数据到 佳明国际区</summary>

<br>

- 如果你只想同步 `type running` 使用参数 --only-run
  **The Python version must be >=3.10**

#### 获取佳明 CN 的密钥

在终端中输入以下命令

```bash
python run_page/get_garmin_secret.py ${your email} ${your password} --is-cn
```

#### 获取佳明全球的密钥

在终端中输入以下命令

```bash
python run_page/get_garmin_secret.py ${your email} ${your password}
```

#### 同步 佳明 CN 到 佳明全球

在终端中输入以下命令

```bash
python run_page/garmin_sync_cn_global.py ${garmin_cn_secret_string} ${garmin_secret_string}
```

</details>

### Nike Run Club New

<details>
<summary>Get your <code>Nike Run Club</code> data</summary>

<br>

> Please note:由于 nike run club 已经在中国大陆停止运营，所以只能通过 vpn 的方式进行登录。在开始之前先确认自己是全局的非中国大陆的代理，能够正确的访问`nike.com`而不是`nike.com.cn` 如下图所示。

![nike.com](https://github.com/user-attachments/assets/8ce6ae8f-4bc6-4522-85ec-3e5b7590e96d)
<br>

1. 登录/注册 [NikeRunClub](https://www.nike.com/) 账号
   ![login](https://github.com/user-attachments/assets/659341fb-4abf-491e-bda7-bfca968921b3)
2. 登录成功后，键盘打开 F12->Application->localstorage-> 复制键为`https://www.nike.com`的值中的`access_token`的内容。
   ![developer_mode](https://github.com/user-attachments/assets/c932318d-a123-4505-8fd8-b46946c25d29)
3. 在根目录执行，你应该就可以看到下图中的内容，然后你就可以正常在你的手机版 NRC 里登录你的账号了：

   ```bash
   python run_page/nike_sync.py ${access_token}
   ```

   如果你同步了一次（已经完成同步）想继续同步新的

   ```bash
   python run_page/nike_sync.py ${access_token} --continue-sync
   ```

   ![tg_image_166091873](https://github.com/user-attachments/assets/9d4851d6-849a-4bb7-8ffe-5358fa7328b2)

   如果你想自动化同步 NRC 中的运动数据，去 [issue692](https://github.com/yihong0618/running_page/issues/692#issuecomment-2218849713)中查看相关内容。

</details>

### Nike Run Club

<details>
<summary>获取 Nike Run Club 数据</summary>

<br>

> 请注意：当您选择将 running_page 部署在自己的服务器上时，由于 Nike 已经封禁了一部分 IDC 的服务器 IP 段，您的服务器可能不能正常同步 Nike Run Club 的数据并显示 `403 error` ，这时您将不得不选择其他的托管方式。

获取 Nike 的 refresh_token

**全部需要在大陆以外的全局 ip 下进行。**

![example img](https://user-images.githubusercontent.com/67903793/282300381-4e7437d0-65a9-4eed-93d1-2b70e360215f.png)

1. 在这里登陆[website](https://unite.nike.com/s3/unite/mobile.html?androidSDKVersion=3.1.0&corsoverride=https%3A%2F%2Funite.nike.com&uxid=com.nike.sport.running.droid.3.8&backendEnvironment=identity&view=login&clientId=VhAeafEGJ6G8e9DxRUz8iE50CZ9MiJMG), 打开 F12 在浏览器抓 login -> XHR -> get the `refresh_token` from login api

2. 复制 `refresh_token` 之后可以添加在 GitHub Secrets 中，也可以直接在命令行中使用

> Chrome 浏览器：按下 F12 打开浏览器开发者工具，点击 Application 选项卡，来到左侧的 Storage 面板，点击展开 Local storage，点击下方的 <https://unite.nike.com>。接着点击右侧的 com.nike.commerce.nikedotcom.web.credential Key，下方会分行显示我们选中的对象，可以看到 refresh_token，复制 refresh_token 右侧的值。Safari 浏览器：在 Safari 打开 Nike 的网页后，右击页面，选择「检查元素」，打开浏览器开发者工具。点击「来源」选项卡，在左侧找到 XHR 文件夹，点击展开，在下方找到 login 文件并单击，在右侧同样可以看到 refresh_token，复制 refresh_token 右侧的值。

```bash
python run_page/nike_sync.py ${nike refresh_token}
```

示例：

```bash
python run_page/nike_sync.py eyJhbGciThiMTItNGIw******
```

![example img](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/nike_sync_%20example.png)

</details>

### Strava

<details>
<summary>获取 Strava 数据</summary>

<br>

1. 注册/登陆 [Strava](https://www.strava.com/) 账号
2. 登陆成功后打开 [Strava Developers](http://developers.strava.com) -> [Create & Manage Your App](https://strava.com/settings/api)

3. 创建 `My API Application`
   输入下列信息：
   ![My API Application](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/strava_settings_api.png)
   创建成功：
   ![Created Successfully](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/created_successfully_1.png)
4. 使用以下链接请求所有权限
   将 ${your_id} 替换为 My API Application 中的 Client ID 后访问完整链接

   ```plaintext
   https://www.strava.com/oauth/authorize?client_id=${your_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all,profile:write,activity:write
   ```

   Example:

   ```plaintext
   https://www.strava.com/oauth/authorize?client_id=115321&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all,profile:write,activity:write
   ```

   ![get_all_permissions](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_all_permissions.png)

5. 提取授权后返回链接中的 code 值
   例如：

   ```plaintext
   http://localhost/exchange_token?state=&code=1dab37edd9970971fb502c9efdd087f4f3471e6e&scope=read,activity:write,activity:read_all,profile:write,profile:read_all,read_all
   ```

   `code` 数值为：

   ```plaintext
   1dab37edd9970971fb502c9efdd087f4f3471e6
   ```

   ![get_code](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_code.png) 6. 使用 Client_id、Client_secret、Code 请求 refresh_token
   在 `终端/iTerm` 中执行：

   ```bash
   curl -X POST https://www.strava.com/oauth/token \
   -F client_id=${Your Client ID} \
   -F client_secret=${Your Client Secret} \
   -F code=${Your Code} \
   -F grant_type=authorization_code
   ```

   示例：

   ```bash
   curl -X POST https://www.strava.com/oauth/token \
   -F client_id=12345 \
   -F client_secret=b21******d0bfb377998ed1ac3b0 \
   -F code=d09******b58abface48003 \
   -F grant_type=authorization_code
   ```

   ![get_refresh_token](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_refresh_token.png)

6. 同步数据至 Strava
   在项目根目录执行：

   > 第一次同步 Strava 数据时需要更改在 strava_sync.py 中的第 12 行代码 False 改为 True，运行完成后，再改为 False。

   仅同步跑步数据，添加参数 --only-run

   ```bash
   python run_page/strava_sync.py ${client_id} ${client_secret} ${refresh_token}
   ```

   其他资料参见
   <https://developers.strava.com/docs/getting-started>
   <https://github.com/barrald/strava-uploader>
   <https://github.com/strava/go.strava>

</details>

### TCX_to_Strava

<details>
<summary>上传所有的 tcx 格式的跑步数据到 strava</summary>

<br>

1. 完成 strava 的步骤
2. 把 tcx 文件全部拷贝到 TCX_OUT 中
3. 在项目根目录下执行：

```bash
python run_page/tcx_to_strava_sync.py ${client_id} ${client_secret} ${strava_refresh_token}
```

示例：

```bash
python run_page/tcx_to_strava_sync.py xxx xxx xxx
或
python run_page/tcx_to_strava_sync.py xxx xxx xxx --all
```

> 如果你已经上传过需要跳过判断增加参数 `--all`

</details>

### TCX_to_Garmin

<details>
<summary>上传所有的 tcx 格式的跑步数据到 Garmin</summary>

<br>

1. 完成 garmin 的步骤
2. 把 tcx 文件全部拷贝到 TCX_OUT 中
3. 在项目根目录下执行：

```bash
python3 run_page/tcx_to_garmin_sync.py ${{ secrets.GARMIN_SECRET_STRING_CN }} --is-cn
```

示例：

```bash
python run_page/tcx_to_garmin_sync.py xxx --is-cn
或佳明国际
python run_page/tcx_to_garmin_sync.py xxx
```

> 如果你已经上传过需要跳过判断增加参数 `--all`

</details>

### GPX_to_Strava

<details>
<summary>上传所有的 gpx 格式的跑步数据到 strava</summary>

<br>

1. 完成 strava 的步骤
2. 把 gpx 文件全部拷贝到 GPX_OUT 中
3. 在项目根目录下执行：

   ```bash
   python run_page/gpx_to_strava_sync.py ${client_id} ${client_secret} ${strava_refresh_token}
   ```

   示例：

   ```bash
   python run_page/gpx_to_strava_sync.py xxx xxx xxx
   或
   python run_page/gpx_to_strava_sync.py xxx xxx xxx --all
   ```

4. 如果你已经上传过需要跳过判断增加参数 `--all`

</details>

### Nike+Strava

<details>
<summary>获取 <code>Nike Run Club</code> 的跑步数据然后同步到 Strava</summary>

<br>

1. 完成 nike 和 strava 的步骤
2. 在项目根目录下执行：

```bash
python run_page/nike_to_strava_sync.py ${nike_refresh_token} ${client_id} ${client_secret} ${strava_refresh_token}
```

示例：

```bash
python run_page/nike_to_strava_sync.py eyJhbGciThiMTItNGIw******  xxx xxx xxx
```

</details>

### Garmin_to_Strava

<details>
<summary>获取你的<code>佳明</code> 的跑步数据，然后同步到 Strava</summary>

<br>

1. 完成 garmin 和 strava 的步骤
2. 在项目根目录下执行：

   ```bash
   python run_page/garmin_to_strava_sync.py  ${client_id} ${client_secret} ${strava_refresh_token} ${garmin_secret_string} --is-cn
   ```

   示例：

   ```bash
   python run_page/garmin_to_strava_sync.py  xxx xxx xxx xx xxx
   ```

</details>

### Strava_to_Garmin

<details>
<summary>获取你的<code>Strava</code> 的跑步数据然后同步到 Garmin</summary>

<br>

1. 完成 garmin 和 strava 的步骤，同时，还需要在 GitHub Actions secret 那新增 Strava 配置：`secrets.STRAVA_EMAIL`、`secrets.STRAVA_PASSWORD`, `secrets.STRAVA_JWT`, 注意: `STRAVA_JWT` 优先级比 `STRAVA_EMAIL` 和 `STRAVA_PASSWORD` 高， `STRAVA_JWT` 为Strava 网页端登录后 Cookie 的`strava_remember_token`字段

2. 在项目根目录下执行：

   ```bash
   python run_page/strava_to_garmin_sync.py ${{ secrets.STRAVA_CLIENT_ID }} ${{ secrets.STRAVA_CLIENT_SECRET }} ${{ secrets.STRAVA_CLIENT_REFRESH_TOKEN }}  ${{ secrets.GARMIN_SECRET_STRING }} ${{ secrets.STRAVA_EMAIL }} ${{ secrets.STRAVA_PASSWORD }}
   ```

   如果你的佳明账号是中国区，执行如下的命令：

   ```bash
   python run_page/strava_to_garmin_sync.py ${{ secrets.STRAVA_CLIENT_ID }} ${{ secrets.STRAVA_CLIENT_SECRET }} ${{ secrets.STRAVA_CLIENT_REFRESH_TOKEN }}  ${{ secrets.GARMIN_SECRET_STRING_CN }} ${{ secrets.STRAVA_EMAIL }} ${{ secrets.STRAVA_PASSWORD }} --is-cn
   ```

   如果要在同步到 Garmin 的运动记录中添加 Garmin 设备信息，需要添加`--use_fake_garmin_device`参数，这将在同步的 Garmin 锻炼记录中添加一个 Garmin 设备（默认情况下为 `Garmin Forerunner 245`，您可以在`garmin_device_adaptor.py`中更改设备信息），运动记录中有了设备信息之后就可以同步到其他 APP 中，比如数字心动（攒上马积分）这类不能通过 Apple Watch 同步的 APP，当然也可以同步到 Keep，悦跑圈，咕咚等 APP。

   <img width="830" alt="image" src="https://github.com/yihong0618/running_page/assets/8613196/b5076942-3133-4c89-ad66-a828211667dc">

   最终执行的命令如下：

   ```bash
   python run_page/strava_to_garmin_sync.py ${{ secrets.STRAVA_CLIENT_ID }} ${{ secrets.STRAVA_CLIENT_SECRET }} ${{ secrets.STRAVA_CLIENT_REFRESH_TOKEN }}  ${{ secrets.GARMIN_SECRET_STRING_CN }} ${{ secrets.STRAVA_EMAIL }} ${{ secrets.STRAVA_PASSWORD }} --use_fake_garmin_device
   ```

   > 注意：**首次初始化的时候，如果你有大量的 strava 跑步数据，可能有些数据会上传失败，只需要多重试几次即可。**

</details>

### Coros 高驰

<details>
<summary>获取您的 Coros 高驰 数据</summary>

#### 在终端中输入以下命令

```bash
python run_page/coros_sync.py ${{ secrets.COROS_ACCOUNT }} ${{ secrets.COROS_PASSWORD }}
```

#### 修改 `run_data_sync.yml` 中 `env.RUN_TYPE: coros`

#### 设置 github action 中 Coros 高驰信息

- 在 github action 中配置 `COROS_ACCOUNT`，`COROS_PASSWORD` 参数

  ![github-action](https://img3.uploadhouse.com/fileuploads/30980/3098042335f8995623f8b50776c4fad4cf7fff8d.png)

</details>

### Keep_to_Strava

<details>
<summary>获取您的 Keep 数据，然后同步到 Strava</summary>
</details>

示例：

```bash
python run_page/keep_to_strava_sync.py ${your mobile} ${your password} ${client_id} ${client_secret} ${strava_refresh_token} --sync-types running cycling hiking
```

#### 解决的需求

1. 适用于由 Strava 总览/展示数据，但是有多种运动类型，且数据来自不同设备的用户。
2. 适用于期望将华为运动健康/OPPO 健康等数据同步到 Strava 的用户 (前提是手机 APP 端已经开启了和 Keep 之间的数据同步)。
3. 理论上华为/OPPO 等可以通过 APP 同步到 Keep 的设备，均可通过此方法自动同步到 Strava，目前已通过测试的 APP 有
   - 华为运动健康：户外跑步，户外骑行，户外步行。

#### 特性以及使用细节

1. 与 Keep 相似，但是由 keep_to_strava_sync.py 实现，不侵入 data.db 与 activities.json。因此不会出现由于同时使用 keep_sync 和 strava_sync 而导致的数据重复统计/展示问题。
2. 上传至 Strava 时，会自动识别为 Strava 中相应的运动类型，目前支持的运动类型为 running, cycling, hiking。
3. run_data_sync.yml 中的修改：

   ```yaml
   RUN_TYPE: keep_to_strava_sync
   ```

</details>

### Total Data Analysis

<details>
<summary>生成数据展示</summary>

<br>

- 生成数据展示 SVG
- 展示效果：[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/master/assets/github.svg)、[点击查看](https://raw.githubusercontent.com/yihong0618/running_page/28fa801e4e30f30af5ae3dc906bf085daa137936/assets/grid.svg)

> 感兴趣的同学可以改下方参数 (--special-distance 10 --special-distance2 20, 10km~20km 展示为 special-color1 20km 以上展示为 special-color2, --min-distance 10.0 用来筛选 10km 以上的)

```bash
python run_page/gen_svg.py --from-db --title "${{ env.TITLE }}" --type github --athlete "${{ env.ATHLETE }}" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
```

```bash
python run_page/gen_svg.py --from-db --title "${{ env.TITLE_GRID }}" --type grid --athlete "${{ env.ATHLETE }}"  --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
```

生成年度环形数据

```bash
python run_page/gen_svg.py --from-db --type circular --use-localtime
```

生成如果一生只有 1000 个月的 Runner Month of Life

```bash
python3 run_page/gen_svg.py --from-db --type monthoflife --birth 1989-03 --special-distance 10 --special-distance2 20 --special-color '#f9d367'  --special-color2 '#f0a1a8' --output assets/mol.svg --use-localtime --athlete yihong0618 --title 'Runner Month of Life'
```

自动生成分享图 GPT gpt-image-1([last one](./PNG_OUT/share_image_2025-04-29.png))

默认最后一次

```bash
python3 run_page/auto_share_sync.py --api_key xxxxxxxxx --base_url xxxxxxxx
```

如果是特定的日子的跑步分享

```bash
python3 run_page/auto_share_sync.py --api_key xxxxxxxxx --base_url xxxxxxxx --date 2023-11-11
```

如果你想自动化 auto share 可以参考这个[链接](https://github.com/yihong0618/run/blob/master/.github/workflows/run_data_sync.yml#L235-242)

更多展示效果参见：
<https://github.com/flopp/GpxTrackPoster>

</details>

## server(recommend vercel)

<details>
<summary>使用 Vercel 部署</summary>

<br>

1. vercel 连接你的 GitHub repo

   ![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)

2. import repo

   ![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)

3. 等待部署完毕
4. 访问

</details>

<details>
<summary> 使用 Cloudflare 部署 </summary>

<br>

1. 登录到 [Cloudflare 仪表板](https://dash.cloudflare.com)。

2. 在左侧选择 `Workers 和 Pages`。

3. 点击 `创建应用程序` 后选择 `Pages` 页面，链接您的 GitHub 账户并选择 `running_page` 仓库，点击 `开始设置`。

4. 下滑到 `构建设置`，在 `框架预设` 中选择 `Create React App`，将 `构建输出目录` 设置为 `dist`。

5. 下滑点击 `环境变量 (高级)`，并添加一个如下的变量：

   > 变量名称 = `PYTHON_VERSION`, 值 = `3.11`

6. 点击 `保存并部署`，完成部署。

</details>

<details>
<summary> 部署到 GitHub Pages </summary>

<br>

1. 进入仓库的 "Settings -> GitHub Pages -> Source"，选择 "GitHub Actions"

2. 进入仓库的 "Actions -> Workflows -> All Workflows"，选择左侧面板的 "Run Data Sync"，然后点击 "Run workflow"

   - "Run Data Sync" 将更新数据，然后触发 "Publish GitHub Pages" 工作流
   - 确认工作流运行没有错误

3. 打开网站检查结果

   - 如果网站没有反映最新数据，请使用“F5”刷新页面
   - 某些浏览器 (比如 Chrome) 可能缓存网页不刷新，您需要使用 Ctrl+F5 (Windows) 或 Shift+Cmd+r (Mac) 强制清除缓存并重新加载页面

4. 为 GitHub Actions 添加代码提交权限，访问仓库的 `Settings > Actions > General`页面，找到 `Workflow permissions` 的设置项，将选项配置为 `Read and write permissions`，支持 CI 将运动数据更新后提交到仓库中。

5. 如果想把你的 running_page 部署在 xxx.github.io 而不是 xxx.github.io/run_page 亦或是想要添加自定义域名于 GitHub Pages，需要做三点

   - 修改你的 fork 的 running_page 仓库改名为 xxx.github.io, xxx 是你 github 的 username
   - 修改 gh-pages.yml 中的 Build 模块，删除 `${{ github.event.repository.name }}` 改为`run: PATH_PREFIX=/ pnpm build` 即可
   - 修改 src/static/site-metadata.ts 中 `siteUrl: ''` 或是添加你的自定义域名，`siteUrl: '[your_own_domain]'`，即可

</details>

## GitHub Actions

> Fork 的同学请一定不要忘了把 GitHub Token 改成自己的，否则会 push 到我的 repo 中，谢谢大家。

<details>
<summary>修改 GitHub Actions Token</summary>

<br>

Actions [源码](https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
需要做如下步骤

1. 更改成你的 app type 及 info

   ![image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)

2. 在 `repo Settings` > `Secrets` 中增加你的 secret (只添加你需要的即可)

   ![image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)

   我的 secret 如下

   ![image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png)

</details>

## 快捷指令

<details>

<summary>使用 iOS 的 Shortcuts 实现自动化</summary>

<br>

下面拿 keep app 举例，当结束跑步后关闭 app，然后自动触发 Actions 更新数据。

1. 拿到项目的 actions id（需要自行申请 token）

   ```shell
   curl https://api.github.com/repos/yihong0618/running_page/actions/workflows -H "Authorization: token d8xxxxxxxxxx" # change to your config
   ```

   <center><img src="https://cdn.jujimeizuo.cn/blog/2023/10/get-action-id.jpg" alt="get-action-id"></center>

2. 结合快捷指令

   1. 通过 iCloud 获取 [running-page-shortcuts-template](https://www.icloud.com/shortcuts/4a5807a98b9a4e359815ff179c62bacb)
   2. 修改下图字典参数

   <center> <img src="https://cdn.jujimeizuo.cn/blog/2023/10/running-page-template.jpg"> </center>

3. 自动化

<center>
<img src="https://cdn.jujimeizuo.cn/blog/2023/10/new-automation.png" width=20% height=20%>
<img src="https://cdn.jujimeizuo.cn/blog/2023/10/select-close.png" width=20% height=20%>
<img src="https://cdn.jujimeizuo.cn/blog/2023/10/select-shortcut.png" width=20% height=20%>
<img src="https://cdn.jujimeizuo.cn/blog/2023/10/finish-automation.png" width=20% height=20%>
</center>

</details>

## GitHub Cache

<details>
<summary>把数据文件放在 GitHub Cache 中</summary>

<br>

`run_data_sync.yml` 中的 `SAVE_DATA_IN_GITHUB_CACHE` 设置为 `true` 时，可以把脚本抓取和中间产生的数据文件放到 GitHub Actions Cache 中。这样可以让你的 GitHub commit 历史和目录保持干净。

如果你用 `GitHub Pages` 部署建议把这个值设置成 `true`。

</details>

# Fit 文件

测试发现，不同厂商在写 fit 文件的时候有略微差异。

已调试设备：

- [x] 佳明手表
- [x] 迈金码表

如果发现自己的 fit 文件解析有问题。可以提 issue。

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
- [x] 支持不同的运动类型

# 参与项目

- 任何 Issues PR 均欢迎。
- 可以提交 PR share 自己的 Running page 在 README 中。
- 提交 PR 前，使用 black 对 Python 代码进行格式化。(`black .`)

# 特别感谢

- @[flopp](https://github.com/flopp) 特别棒的项目 [GpxTrackPoster](https://github.com/flopp/GpxTrackPoster)
- @[danpalmer](https://github.com/danpalmer) 原始的 UI 设计
- @[shaonianche](https://github.com/shaonianche) icon 设计及文档
- @[geekplux](https://github.com/geekplux) 帮助及鼓励，重构了前端代码，学到了不少
- @[ben-29](https://github.com/ben-29) 搞定了咕咚，和我一起搞定了悦跑圈，太厉害了
- @[MFYDev](https://github.com/MFYDev) Wiki

# 推荐的 Forks

- @[gongzili456](https://github.com/gongzili456) for [摩托车骑行版本](https://github.com/gongzili456/running_page)
- @[ben-29](https://github.com/ben-29) for [多种运动类型支持](https://github.com/ben-29/workouts_page)
- @[geekplux](https://github.com/geekplux) for [多种运动类型支持](https://github.com/geekplux/activities)

# 赞赏

谢谢就够了

# Raycast 插件

<a title="Install running-page Raycast Extension" href="https://www.raycast.com/Lemon/running-page"><img src="https://www.raycast.com/Lemon/running-page/install_button@2x.png?v=1.1" height="64" alt="" style="height: 64px;"></a>

# FAQ

- Strava 100 每 15 分钟的请求，1000 每日限制

  <https://www.strava.com/settings/api>
  <https://developers.strava.com/docs/#rate-limiting>

  等待时间限制（这里是 strava 接口请求限制），不要关闭终端，这里会自动执行下一组上传数据

  ```plaintext
  Strava API Rate Limit Exceeded. Retry after 100 seconds
  Strava API Rate Limit Timeout. Retry in 799.491622 seconds
  ```

- vercel git

  如果想 ignore gh-pages 可以在 `settings` -> `build` -> `Ignored Build Step` -> `Custom` 输入命令：

  ```bash
  if [ "$VERCEL_GIT_COMMIT_REF" != "gh-pages" ]; then exit 1; else exit 0;
  ```
