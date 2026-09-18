# 配置指南

## 概述

本项目的所有配置都集中在根目录的 config.yml 文件中。修改此文件即可完成个性化设置，无需改动源代码。

## 配置文件说明

### 站点信息

`yaml
# 站点标题
site_title: 'Sports Page'
# 站点 URL
site_url: 'https://sports-page.lczhuigz.cn'
# 站点 Logo URL
site_logo: 'https://blog.lczhuigz.cn/images/fav-icon/fav-icon.jpg'
# 站点描述
site_description: 'Personal site and blog'
# GitHub 仓库 URL
repo_url: 'https://github.com/lczhuigz/running_page'

# 导航链接
nav_links:
  - name: 'Blog'
    url: 'https://blog.lczhuigz.cn'
  - name: 'About'
    url: 'https://blog.lczhuigz.cn/about'
`

### 地图配置

`yaml
# 地图提供商: maptiler | mapbox | openfreemap
map_provider: 'maptiler'

# 地图样式
map_style_light: 'streets-light'
map_style_dark: 'streets-dark'

# API Token (推荐通过 GitHub Secrets 配置)
mapbox_token: ''
maptiler_token: ''
`

#### 地图提供商说明

1. **OpenFreeMap** (免费，无需 Token)
   - 完全免费，无需注册
   - 样式选项: right, dark, liberty
   - 适合个人项目

2. **MapTiler** (推荐)
   - 注册地址: https://cloud.maptiler.com
   - 免费套餐: 每月 100,000 次加载
   - 样式选项丰富

3. **Mapbox**
   - 注册地址: https://account.mapbox.com
   - 免费套餐: 每月 50,000 次加载
   - 功能强大

### 轨迹显示配置

`yaml
# 是否显示轨迹起点和终点标记
show_start_end_markers: true
# 起点标记颜色 (白色小旗子)
start_marker_color: '#ffffff'
# 终点标记颜色 (红色小旗子)
end_marker_color: '#ef4444'
`

### 外观配置

`yaml
# 头像 URL
avatar: 'https://blog.lczhuigz.cn/images/fav-icon/fav-icon.jpg'
# 默认语言: zh (中文) | en (英文)
locale: zh
# 默认主题: system | light | dark
theme: system
# 主题预设: dashboard | classic
theme_preset: dashboard
`

### 运动目标

`yaml
goals:
  all:
    yearly: 2000
    monthly: 300
    weekly: 35
    unit: distance

  Run:
    yearly: 2000
    monthly: 150
    weekly: 35
    unit: distance
`

## 配置 GitHub Secrets

为了安全起见，地图 API Token 推荐通过 GitHub Secrets 配置。

### 步骤

1. **获取 API Token**
   - MapTiler: 访问 https://cloud.maptiler.com/account/keys/
   - Mapbox: 访问 https://account.mapbox.com/access-tokens/

2. **添加 GitHub Secret**
   - 进入你的 GitHub 仓库
   - 点击 Settings -> Secrets and variables -> Actions
   - 点击 New repository secret
   - 添加以下 Secret:
     - Name: MAPTILER_TOKEN, Value: 你的 MapTiler API Key
     - Name: MAPBOX_TOKEN, Value: 你的 Mapbox Access Token

3. **配置环境变量 (可选)**
   
   如果你使用 Vercel 或其他平台部署，需要在平台中配置环境变量:
   - VITE_MAPTILER_TOKEN: MapTiler API Key
   - VITE_MAPBOX_TOKEN: Mapbox Access Token

### 本地开发

在本地开发时，可以在项目根目录创建 .env 文件:

`env
VITE_MAPTILER_TOKEN=your_maptiler_token_here
VITE_MAPBOX_TOKEN=your_mapbox_token_here
`

## 常见问题

### Q: 如何切换地图提供商？

修改 config.yml 中的 map_provider 字段:

`yaml
# 使用 MapTiler
map_provider: 'maptiler'

# 使用 Mapbox
map_provider: 'mapbox'

# 使用免费的 OpenFreeMap
map_provider: 'openfreemap'
`

### Q: 如何隐藏起点/终点标记？

修改 config.yml:

`yaml
show_start_end_markers: false
`

### Q: 如何修改页面标题？

修改 config.yml:

`yaml
site_title: '你的标题'
`

### Q: 如何添加导航链接？

修改 config.yml:

`yaml
nav_links:
  - name: 'Blog'
    url: 'https://your-blog.com'
  - name: 'About'
    url: 'https://your-blog.com/about'
  - name: 'GitHub'
    url: 'https://github.com/your-username'
`

## 更新日志

- 支持 MapTiler、Mapbox 和 OpenFreeMap 三种地图提供商
- 地图 Token 支持通过 GitHub Secrets 配置
- 添加轨迹起点/终点标记功能
- 页面标题"跑步记录"改为"运动记录"
- 活动记录表格添加海拔爬升数据
