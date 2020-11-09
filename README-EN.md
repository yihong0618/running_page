![running_page](https://socialify.git.ci/yihong0618/running_page/image?description=1&font=Inter&forks=1&issues=1&language=1&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fshaonianche%2Fgallery%2Fmaster%2Frunning_page%2Frunning_page_logo_150*150.jpg&owner=1&pulls=1&stargazers=1&theme=Light)


# [Create a personal running home page](https://yihong.run/running)

[简体中文](https://github.com/yihong0618/running_page/blob/master/README.md) | English

## [Runner's Page Show](https://github.com/yihong0618/running_page/issues/12)

| Runner | page | App |
| ------- | ------- | ------- |
| [shaonianche](https://github.com/shaonianche) | https://run.duangfei.org | Nike |
| [yihong0618](https://github.com/yihong0618) | https://yihong.run/running | Nike |
| [superleeyom](https://github.com/superleeyom) | https://running.leeyom.top | Keep |
| [geekplux](https://github.com/geekplux) | https://activities.geekplux.com | Nike |
| [guanlan](https://github.com/guanlan) | https://grun.vercel.app | Strava |
| [tuzimoe](https://github.com/tuzimoe) | https://run.tuzi.moe | Nike |
| [ben_29](https://github.com/ben-29) | https://running.ben29.xyz | Strava |
| [kcllf](https://github.com/kcllf) | https://running-tau.vercel.app | Garmin-cn |



## Features

1. GitHub Actions manages automatic synchronization of runs and generation of new pages.
2. Gatsby-generated static pages, fast
3. Support for Vercel (recommended) automated deployment
4. React Hooks
5. Mapbox for map display
6. Nike and Runtastic (Adidas Run) 

> automatically backup gpx data for easy backup and uploading to other software.



## Support

- **[Strava](#strava)**
- **[Nike Run Club](#NikeRunClub)**
- **[Runtastic(Adidas Run)](#Runtastic(AdidasRun))**
- **[Garmin](#Garmin)**
- **[Garmin-cn](#Garmin-CN(China))**

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
### Delete my test data
```bash
rm scripts/data.db GPX_OUT/* activities/*
```
OR
```bash
rm scripts/data.db
rm GPX_OUT/*
rm activities/*
```

### Modifying Mapbox token in `src/utils/const.js`

> Suggested changes to your own [Mapbox token](https://www.mapbox.com/)

```javascript
const MAPBOX_TOKEN = 'pk.eyJ1IjoieWlob25nMDYxOCIsImEiOiJja2J3M28xbG4wYzl0MzJxZm0ya2Fua2p2In0.PNKfkeQwYuyGOTT_x9BJ4Q';
```

## Download your Garmin/Garmin-CN/Runtastic(Adidas Run)/Nike Run Club/Strava data

### Garmin

<details>
<summary>Get your Garmin data</summary>

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
<summary>Get your Garmin-CN data</summary>

```python
python3(python) scripts/garmin_sync.py ${your email} ${your password} --is-cn
```
example：
```python
python3(python) scripts/garmin_sync.py example@gmail.com example --is-cn
```
</details>

### Runtastic(Adidas Run)

<details>
<summary>Get your `Runtastic` data</summary>

```python
python3(python) scripts/runtastic_sync.py ${your email} ${your password}
```
example：

```python
python3(python) scripts/runtastic_sync.py example@gmail.com example
```
</details>

### Nike Run Club

<details>
<summary>Get your `Nike Run Club` data</summary>

Get Nike's `refresh_token`
1. Login [Nike](https://www.nike.com) website
2. In Develop -> Application-> Storage -> https:unite.nike.com look for `refresh_token`

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

### Runtastic(Adidas Run)/Nike Run Club Data Analysis

<details>
<summary> Running data display </summary>

- Generate SVG data display
- Display of results：[Click to view](https://raw.githubusercontent.com/yihong0618/running_page/master/assets/github.svg)、[Click to view](https://raw.githubusercontent.com/yihong0618/running_page/28fa801e4e30f30af5ae3dc906bf085daa137936/assets/grid.svg)

```
python scripts/gen_svg.py --from-db --title "${{ env.TITLE }}" --type github --athlete "${{ env.ATHLETE }}" --special-distance 10 --special-distance2 20 --special-color yellow --special-color2 red --output assets/github.svg --use-localtime --min-distance 0.5
```

```
python scripts/gen_svg.py --from-db --title "${{ env.TITLE_GRID }}" --type grid --athlete "${{ env.ATHLETE }}"  --output assets/grid.svg --min-distance 10.0 --special-color yellow --special-color2 red --special-distance 20 --special-distance2 40 --use-localtime
```
For more display effects, see:     
https://github.com/flopp/GpxTrackPoster

</details>

### Strava

<details>
<summary> Get your `Strava` data </summary>

1. Sign in/Sign up [Strava](https://www.strava.com/) account
2. Open after successful Signin [Strava Developers](http://developers.strava.com) -> [Create & Manage Your App](https://strava.com/settings/api)

3. Create `My API Application`   
Enter the following information：
![My API Application](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/strava_settings_api.png)
Created successfully：
![](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/created_successfully_1.png)

4. Use the link below to request all permissions   
Replace ${your_id} in the link with `My API Application` Client ID 
```
https://www.strava.com/oauth/authorize?client_id=${your_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all,profile:write,activity:write
```
![get_all_permissions](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_all_permissions.png)

5. Get the `code` value in the link   
example：
```
http://localhost/exchange_token?state=&code=1dab37edd9970971fb502c9efdd087f4f3471e6e&scope=read,activity:write,activity:read_all,profile:write,profile:read_all,read_all
```
`code` value：
```
1dab37edd9970971fb502c9efdd087f4f3471e6
```
![get_code](https://raw.githubusercontent.com/shaonianche/gallery/master/running_page/get_code.png)

6. Use `Client_id`、`Client_secret`、`Code` get `refresch_token`   
    
Execute in `Terminal/iTerm`:
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

## server(recommendation vercel)

<details>
<summary> Use vercel deploy </summary>

1. vercel connects to your GitHub repo.
![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)
2. import repo
![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)
2. Awaiting completion of deployment
3. Visits

</details>

## GitHub Actions 



<details>
<summary> Modifying information in `GitHub Actions`  </summary>

Actions [source code](https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
The following steps need to be taken
1. change to your app type and info
![image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)
Add your secret in repo Settings > Secrets (add only the ones you need).
![image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)
My secret is as follows
![image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png)
3. add your [GitHub secret](https://github.com/settings/tokens) and have the same name as the GitHub secret in your project.
![image](https://user-images.githubusercontent.com/15976103/94450721-2f222100-01e0-11eb-94a7-ef1f06fc0a59.png)

</details>

# TODO

- [ ] Complete this document.
- [x] Support Garmin, Garmin China
- [ ] Support the Joy Runner
- [ ] support for nike+strava, runtastic+strava
- [ ] Support English
- [ ] Refine the code
- [ ] add new features

# Contribution

Before submitting PR:
- Format Python code with Black

# Special thanks

- @[flopp](https://github.com/flopp)
- @[shaonianche](https://github.com/shaonianche)
- @[geekplux](https://github.com/geekplux)

