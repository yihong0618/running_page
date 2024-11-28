## note1: use v2.0 need change vercel setting from Gatsby to Vite

## note2: 2023.09.26 garmin need secret_string(and in Actions) get `python run_page/garmin_sync.py ${secret_string}` if cn `python run_page/garmin_sync.py ${secret_string} --is-cn`

## note3: 2024.08.19: Added `Elevation Gain` field
  - For old data: To include `Elevation Gain` for past activities, perform a full reimport

# [打造个人户外运动主页](http://workouts.ben29.xyz)

![screenshot](https://user-images.githubusercontent.com/6956444/163125711-24d0ad99-490d-4c04-b89f-5b7fe776eb38.png)

简体中文 | [English](README.md)

本项目基于 [running_page](https://github.com/yihong0618/running_page/blob/master/README-CN.md) , 添加了支持多种运动类型。部署可参考原项目操作步骤

## 新增特性

1. 支持多种运动类型，如骑行、徒步、游泳
1. 支持 APP 数据获取
   - **[咕咚](#codoon咕咚)** (因咕咚限制单个设备原因，无法自动化)
   - **[行者](#行者)**
1. 支持 [自驾(Google 路书)](#自驾google路书) , 把自驾路线也展示在地图上

## 一些个性化选项

### 自定义运动颜色

- 修改骑行颜色: `src/utils/const.js` 里的 `RIDE_COLOR`

### 新增运动类型

- 修改 `scripts/config.py`, `TYPE_DICT` 增加类型映射关系, `MAPPING_TYPE` 里增加运动类型
- 修改 `src/utils/const.js`, 增加类型标题，并加入到 `RUN_TITLES`
- 修改 `src/utils/util.js` 里的 `colorFromType`, 增加 case 指定颜色; `titleForRun`  增加 case 指定类型标题
- 参考这个 [commit](https://github.com/ben-29/workouts_page/commit/f3a35884d626009d33e05adc76bbc8372498f317)
- 或 [留言](https://github.com/ben-29/workouts_page/issues/20)
---

### Codoon（咕咚）

<details>
<summary>获取您的咕咚数据</summary>

```python
python3(python) run_page/codoon_sync.py ${your mobile or email} ${your password}
```

示例：

```python
python3(python) run_page/codoon_sync.py 13333xxxx xxxx
```

> 注：我增加了 Codoon 可以导出 gpx 功能, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) run_page/codoon_sync.py ${your mobile or email} ${your password} --with-gpx
```

示例：

```python
python3(python) run_page/codoon_sync.py 13333xxxx xxxx --with-gpx
```

> 注：因为登录 token 有过期时间限制，我增加了 refresh_token&user_id 登陆的方式， refresh_token 及 user_id 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/6956444/105690972-9efaab00-5f37-11eb-905c-65a198ad2300.png)

示例：

```python
python3(python) run_page/codoon_sync.py 54bxxxxxxx fefxxxxx-xxxx-xxxx --from-auth-token
```

</details>

### 行者

<details>
<summary>获取您的行者数据</summary>

```python
python3(python) scripts/xingzhe_sync.py ${your mobile or email} ${your password}
```

示例：

```python
python3(python) scripts/xingzhe_sync.py 13333xxxx xxxx
```

> 注：我增加了 行者 可以导出 gpx 功能, 执行如下命令，导出的 gpx 会加入到 GPX_OUT 中，方便上传到其它软件

```python
python3(python) scripts/xingzhe_sync.py ${your mobile or email} ${your password} --with-gpx
```

示例：

```python
python3(python) scripts/xingzhe_sync.py 13333xxxx xxxx --with-gpx
```

> 注：因为登录 token 有过期时间限制，我增加了 refresh_token&user_id 登陆的方式， refresh_token 及 user_id 在您登陆过程中会在控制台打印出来

![image](https://user-images.githubusercontent.com/6956444/106879771-87c97380-6716-11eb-9c28-fbf70e15e1c3.png)

示例：

```python
python3(python) scripts/xingzhe_sync.py w0xxx 185000 --from-auth-token
```

</details>

### 自驾(Google 路书)

<details>
<summary>导入谷歌地图的KML路书</summary>

1. 使用 [谷歌地图](https://www.google.com/maps/d/) ，创建地图(路线放到同一个图层)
2. 把图层导出为 KML 文件
3. 把 kml 文件重命名为 `import.kml`, 放到 `scripts`目录
4. 修改`scripts/kml2polyline.py`, 填入路线相关信息

```
# TODO modify here
# 路线名称
track.name = "2020-10 西藏 Road Trip"
# 开始/结束时间 年月日时分
track.start_time = datetime(2020, 9, 29, 10, 0)
track.end_time = datetime(2020, 10, 10, 18, 0)
# 总路程
distance = 4000  # KM
# 总天数
days = 12
# 平均每天自驾时长
hours_per_day = 6
```

5. 控制台执行以下脚本

```python
python3(python) scripts\kml2polyline.py
```

</details>

# 致谢

- @[yihong0618](https://github.com/yihong0618) 特别棒的项目 [running_page](https://github.com/yihong0618/running_page) 非常感谢
