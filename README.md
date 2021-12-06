<p align="center">
  <img width="150" src="https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/running_page_logo.png" />
</p>

<h3 align="center">
  <a href="https://yihong.run/running"> Create a personal running home page </a>
</h3>

<p align="center">
  <a href="https://github.com/yihong0618/running_page/actions"><img src="https://github.com/yihong0618/running_page/actions/workflows/run_data_sync.yml/badge.svg" alt="Github Action"></a>
  <a href="https://t.me/running_page"><img src="https://badgen.net/badge/icon/join?icon=telegram&amp;label=usergroup" alt="Chat on telegram"></a>
</p>

<p align="center">
  <img src="https://user-images.githubusercontent.com/15976103/98808834-c02f1d80-2457-11eb-9a7c-70e91faa5e30.gif" alt="demo" width="800">
</p>

English | [简体中文](https://github.com/yihong0618/running_page/blob/master/README-CN.md) | [Wiki](https://wiki.mfydev.run/)

## [Runner's Page Show](https://github.com/yihong0618/running_page/issues/12)

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
| [Eished](https://github.com/eished)             | https://run.iknow.fun                      | Keep      |
| [Liuxin](https://github.com/liuxindtc)             | https://liuxin.run                   |  Nike      |

## How it works

![image](https://user-images.githubusercontent.com/15976103/103496454-4294f600-4e79-11eb-9bd6-8eea7a07ddff.png)

## Features

1. GitHub Actions manages automatic synchronization of runs and generation of new pages.
2. Gatsby-generated static pages, fast
3. Support for Vercel (recommended) and GitHub Pages automated deployment
4. React Hooks
5. Mapbox for map display
6. Supports most sports apps such as nike strava...

> automatically backup gpx data for easy backup and uploading to other software.

> Note: If you don't want to make the data public, you can choose strava's fuzzy processing, or private repositories.

## Support

- **[Garmin](#garmin)**
- **[Garmin-CN](#garmin-cnchina)**
- **[Nike Run Club](#nike-run-club)**
- **[Strava](#strava)**
- **[GPX](#GPX)**
- **[Nike_to_Strava(Using NRC Run, Strava backup data)](#Nike_to_Strava)**
- **[Strava_to_Garmin(Using Strava Run, Garmin backup data)](#)**

## Download

Clone or fork the repo.

```
git clone https://github.com/yihong0618/running_page.git
```

## Installation and testing

```
pip3 install -r requirements.txt
yarn install
yarn develop
```

Open your browser and visit http://localhost:8000/

## Local sync data

### Modifying Mapbox token in `src/utils/const.js`

> If you use English please change `IS_CHINESE = false` in `src/utils/const.js`

> Suggested changes to your own [Mapbox token](https://www.mapbox.com/)

```javascript
const MAPBOX_TOKEN =
  'pk.eyJ1IjoieWlob25nMDYxOCIsImEiOiJja2J3M28xbG4wYzl0MzJxZm0ya2Fua2p2In0.PNKfkeQwYuyGOTT_x9BJ4Q';
```

## Custom your page

Find `gatsby-config.js` in the repository directory, find the following content, and change it to what you want.

```javascript
siteMetadata: {
  siteTitle: 'Running Page', #website title
  siteUrl: 'https://yihong.run', #website url
  logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU', #logo img
  description: 'Personal site and blog',
  navLinks: [
    {
      name: 'Blog', #navigation name
      url: 'https://yihong.run/running', #navigation url
    },
    {
      name: 'About',
      url: 'https://github.com/yihong0618/running_page/blob/master/README-CN.md',
    },
  ],
},
```

## Download your running data and do not forget to [generate svg in `total` page](#Total-Data-Analysis).

### GPX

<details>
<summary>Make your <code>GPX</code> data</summary>
<br>

Copy all your gpx files to GPX_OUT or new gpx files

```python
python3(python) scripts/gpx_sync.py
```

</details>

### Garmin

<details>
<summary>Get your <code>Garmin</code> data</summary>
<br>
If you only want to sync `type running` add args --only-run

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password}
```

example：

```python
python3(python) scripts/garmin_sync.py example@gmail.com example
```

</details>

### Garmin-CN(China)

<details>
<summary>Get your <code>Garmin-CN</code> data</summary>
<br>

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password} --is-cn
```

example：

```python
python3(python) scripts/garmin_sync.py example@gmail.com example --is-cn
```

</details>

### Nike Run Club

<details>
<summary>Get your <code>Nike Run Club</code> data</summary>

<br>

**Please note: When you choose to deploy running_page on your own server, due to Nike has blocked some IDC's IP band, maybe your server cannot sync Nike Run Club's data correctly and display `403 error`, then you have to change another way to host it.**

Get Nike's `refresh_token`

1. Login [Nike](https://www.nike.com) website
2. In Develop -> Application-> Storage -> https:unite.nike.com look for `refresh_token`

<br>

![image](https://user-images.githubusercontent.com/15976103/94448123-23812b00-01dd-11eb-8143-4b0839c31d90.png)

3. Execute in the root directory:

```python
python3(python) scripts/nike_sync.py ${nike refresh_token}
```

example：

```python
python3(python) scripts/nike_sync.py eyJhbGciThiMTItNGIw******
```

![example img](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/nike_sync_%20example.png)

</details>

### Strava

<details>
<summary> Get your <code>Strava</code> data </summary>
<br>

1. Sign in/Sign up [Strava](https://www.strava.com/) account
2. Open after successful Signin [Strava Developers](http://developers.strava.com) -> [Create & Manage Your App](https://strava.com/settings/api)

3. Create `My API Application`: Enter the following information

<br>

![My API Application](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/strava_settings_api.png)
Created successfully：

<br>

![](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/created_successfully_1.png)

4. Use the link below to request all permissions: Replace `${your_id}` in the link with `My API Application` Client ID

```
https://www.strava.com/oauth/authorize?client_id=${your_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all,profile:write,activity:write
```

![get_all_permissions](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_all_permissions.png)

5. Get the `code` value in the link

<br>

example：

```
http://localhost/exchange_token?state=&code=1dab37edd9970971fb502c9efdd087f4f3471e6e&scope=read,activity:write,activity:read_all,profile:write,profile:read_all,read_all
```

`code` value：

```
1dab37edd9970971fb502c9efdd087f4f3471e6
```

![get_code](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_code.png)

6. Use `Client_id`、`Client_secret`、`Code` get `refresch_token`: Execute in `Terminal/iTerm`

```
curl -X POST https://www.strava.com/oauth/token \
-F client_id=${Your Client ID} \
-F client_secret=${Your Client Secret} \
-F code=${Your Code} \
-F grant_type=authorization_code
```

example：

```
curl -X POST https://www.strava.com/oauth/token \
-F client_id=12345 \
-F client_secret=b21******d0bfb377998ed1ac3b0 \
-F code=d09******b58abface48003 \
-F grant_type=authorization_code
```

![get_refresch_token](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_refresch_token.png)

7. Sync `Strava` data

```python
python3(python) scripts/strava_sync.py ${client_id} ${client_secret} ${refresch_token}
```

References：  
https://developers.strava.com/docs/getting-started  
https://github.com/barrald/strava-uploader  
https://github.com/strava/go.strava

</details>

### Nike_to_Strava

<details>
<summary>Get your <code>Nike Run Club</code> data and upload to strava</summary>

<br>

1. follow the nike and strava steps
2. Execute in the root directory:

```python
python3(python) scripts/nike_to_strava_sync.py ${nike_refresh_token} ${client_id} ${client_secret} ${strava_refresch_token}
```

example：

```python
python3(python) scripts/nike_to_strava_sync.py eyJhbGciThiMTItNGIw******  xxx xxx xxx
```

</details>

### Total Data Analysis

<details>
<summary> Running data display </summary>
<br>

- Generate SVG data display
- Display of results：[Click to view](https://raw.githubusercontent.com/yihong0618/running_page/master/assets/github.svg)、[Click to view](https://raw.githubusercontent.com/yihong0618/running_page/28fa801e4e30f30af5ae3dc906bf085daa137936/assets/grid.svg)

```
python scripts/gen_svg.py --from-db --title "${{ env.TITLE }}" --type github --athlete "${{ env.ATHLETE }}" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
```

```
python scripts/gen_svg.py --from-db --title "${{ env.TITLE_GRID }}" --type grid --athlete "${{ env.ATHLETE }}"  --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
```

Generate year circular svg show

```
python3(python) scripts/gen_svg.py --from-db --type circular --use-localtime
```

For more display effects, see:  
https://github.com/flopp/GpxTrackPoster

</details>

## server(recommendation vercel)

<details>
<summary> Use <code>Vercel</code> to deploy </summary>
<br>

1. vercel connects to your GitHub repo.

<br>

![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)

2. import repo

<br>

![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)

2. Awaiting completion of deployment
3. Visits

</details>

<details>
<summary> Use <code>Cloudflare</code> to deploy </summary>
<br>

1. Click `Create a project` in `Pages` to connect to your Repo.

2. After clicking `Begin setup`, modify Project's `Build settings`.

3. Select `Framework preset` to `Gatsby`

4. Scroll down, click `Environment variables`, then variable below:

   > Variable name = `PYTHON_VERSION`, Value = `3.7`

5. Click `Save and Deploy`

</details>

<details>
<summary> Deploy to GitHub Pages </summary>

1. If you are using a custom domain for GitHub Pages, open [.github/workflows/gh-pages.yml](.github/workflows/gh-pages.yml), change `fqdn` value to the domain name of your site.

2. (_Skip this step if you're **NOT** using a custom domain_) Modify `gatsby-config.js`, change `pathPrefix` value to the root path. If the repository name is `running_page`, the value will be `/running_page`.

3. Go to repository's `Actions -> Workflows -> All Workflows`, choose `Publish GitHub Pages` from the left panel, click `Run workflow`. Make sure the workflow runs without errors, and `gh-pages` branch is created.

4. Go to repository's `Settings -> GitHub Pages -> Source`, choose `Branch: gh-pages`, click `Save`.
</details>

## GitHub Actions

<details>
<summary> Modifying information in <code>GitHub Actions</code>  </summary>
<br>

Actions [source code](https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
The following steps need to be taken

1. change to your app type and info

<br>

![image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)
Add your secret in repo Settings > Secrets (add only the ones you need).

<br>

![image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)
My secret is as follows

<br>

![image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png) 3. add your [GitHub secret](https://github.com/settings/tokens) and have the same name as the GitHub secret in your project.

<br>

![image](https://user-images.githubusercontent.com/15976103/94450721-2f222100-01e0-11eb-94a7-ef1f06fc0a59.png)

</details>

# TODO

- [x] Complete this document.
- [x] Support Garmin, Garmin China
- [x] support for nike+strava
- [x] Support English
- [x] Refine the code
- [x] add new features
- [ ] tests
- [ ] support the world map
- [ ] support multiple types, like hiking, biking~

# Contribution

- Any Issues PR welcome.
- You can PR share your Running page in README I will merge it.

Before submitting PR:

- Format Python code with `black` (black .)
- Format Python code with `isort` (isort --profile black  **/**/*.py)

# Special thanks

- @[flopp](https://github.com/flopp) great repo [GpxTrackPoster](https://github.com/flopp/GpxTrackPoster)
- @[danpalmer](https://github.com/danpalmer) UI design
- @[shaonianche](https://github.com/shaonianche) icon design and doc
- @[geekplux](https://github.com/geekplux) Friendly help and encouragement, refactored the whole front-end code, learned a lot
- @[MFYDev](https://github.com/MFYDev) Wiki

# Support

No need sponsor, just enjoy it.
