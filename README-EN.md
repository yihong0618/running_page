# [Create a personal running home page](https://yihong.run/running)

[简体中文](https://github.com/yihong0618/running_page/blob/master/README.md) | English

## Features

1. GitHub Actions manages automatic synchronization of runs and generation of new pages.
2. Gatsby-generated static pages, fast
3. Support for Vercel (recommended) automated deployment
4. React Hooks
5. Mapbox for map display
6. Nike and Runtastic (Adidas Run) automatically backup gpx data for easy backup and uploading to other software.

## Support

- Strava
- Nike Run Club
- Runtastic (Adidas Run)

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

## Download your Runtastic(Adidas Run)/Nike Run Club/Strava data
### Runtastic(Adidas Run)

```python
python3(python) scripts/runtastic_sync.py ${your email} ${your password}
```
example：
```python
python3(python) scripts/runtastic_sync.py example@gmail.com example
```
### Nike Run Club

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

### Runtastic(Adidas Run)/Nike Run Club Data Analysis

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

### Strava

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
    References
    https://developers.strava.com/docs/getting-started   
    https://github.com/barrald/strava-uploader   
    https://github.com/strava/go.strava   


## server(recommendation vercel)
1. vercel connects to your GitHub repo.
![image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)
2. import repo
![image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)
2. Awaiting completion of deployment
3. Visits

## GitHub Actions 
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

## My display
![image](https://user-images.githubusercontent.com/15976103/87566339-775b9800-c6f5-11ea-803f-6c2f69801ee4.png)

# TODO

- [ ] Complete this document.
- [ ] Support Garmin, Garmin China
- [ ] Support the Joy Runner
- [ ] support for nike+strava, runtastic+strava
- [ ] Support English
- [ ] Refine the code
- [ ] add new features

# Contribution

Before submitting PR:
- Format Python code with Black

# Special thanks

@[flopp](https://github.com/flopp)

Translated with www.DeepL.com/Translator (free version)
