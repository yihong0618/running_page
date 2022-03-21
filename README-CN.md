
# [打造个人户外运动主页](http://workouts.ben29.xyz) 
简体中文 | [English](README.md)

本项目基于 [running_page](https://github.com/yihong0618/running_page/blob/master/README-CN.md) , 添加了支持多种运动类型。部署可参考原项目操作步骤

## 新增特性
1. 支持多种运动类型，如骑行、徒步、游泳
1. 支持APP数据获取
    - **[咕咚](#codoon咕咚)** (因咕咚限制单个设备原因，无法自动化)
    - **[行者](#行者)**
1. 支持 [自驾(Google路书)](#自驾google路书) , 把自驾路线也展示在地图上 

## 一些个性化选项

### 自定义运动颜色

* 修改骑行颜色: `src/utils/const.js` 里的 `RIDE_COLOR`

### 新增运动类型
* 修改 `scripts/config.py`, `TYPE_DICT` 增加类型映射关系
* 修改 `src/utils/util.js` 里的 `colorFromType`, 增加case

---

# 致谢
- @[yihong0618](https://github.com/yihong0618) 特别棒的项目 [running_page](https://github.com/yihong0618/running_page) 非常感谢
