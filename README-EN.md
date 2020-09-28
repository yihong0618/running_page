# [Create a personal running home page](https://yihong.run/running)

## Characteristics

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

## Installation and testing

- pip3 install -r requirements.txt
- yarn install
- yarn develop

## Local sync data

### Delete my test data

- rm scripts/data.db
- rm GPX_OUT/*
- rm activities/*

### Runtastic (Adidas Run)
``python.
python3(python) scripts/runtastic_sync.py ${your email} ${your password}
```
## Nike Run Club
``python.
python3(python) scripts/nike_sync.py ${nike refresh_token}
```
How to get a nike refresh token
1. Login to the Nike website
2. find the refresh_token in Developer -> Application-> Storage -> https:unite.nike.com
! [image](https://user-images.githubusercontent.com/15976103/94448123-23812b00-01dd-11eb-8143-4b0839c31d90.png)

### Strava
``python.
python3(python) scripts/strava_sync.py ${client_id} ${client_id} ${refresch_token}
```
 How to get to client_id, client_id, refresch_token see https://developers.strava.com/docs/getting-started/
 Or refer to the following items
 1. https://github.com/barrald/strava-uploader
 2. https://github.com/strava/go.strava
 
## server(recommendation vercel)

1. vercel connects to your GitHub repo.
! [image](https://user-images.githubusercontent.com/15976103/94452465-2599b880-01e2-11eb-9538-582f0f46c421.png)
2. import repo
! [image](https://user-images.githubusercontent.com/15976103/94452556-3f3b0000-01e2-11eb-97a2-3789c2d60766.png)
2. Awaiting completion of deployment
3. Visits

## GitHub Actions 
Actions [source code] (https://github.com/yihong0618/running_page/blob/master/.github/workflows/run_data_sync.yml)
The following steps need to be taken
1. change to your app type and info
! [image](https://user-images.githubusercontent.com/15976103/94450124-73f98800-01df-11eb-9b3c-ac1a6224f46f.png)
Add your secret in repo Settings > Secrets (add only the ones you need).
! [image](https://user-images.githubusercontent.com/15976103/94450295-aacf9e00-01df-11eb-80b7-a92b9cd1461e.png)
My secret is as follows
! [image](https://user-images.githubusercontent.com/15976103/94451037-8922e680-01e0-11eb-9bb9-729f0eadcdb7.png)
3. add your [GitHub secret](https://github.com/settings/tokens) and have the same name as the GitHub secret in your project.
! [image](https://user-images.githubusercontent.com/15976103/94450721-2f222100-01e0-11eb-94a7-ef1f06fc0a59.png)

## My display
! [image](https://user-images.githubusercontent.com/15976103/87566339-775b9800-c6f5-11ea-803f-6c2f69801ee4.png)

# TODO

- [ ] Complete this document.
- [ ] Support Garmin, Garmin China
- [ ] Support the Joy Runner
- [ ] support for nike+strava, runtastic+strava
- [ ] Support English
- [ ] Refine the code
- [ ] add new features

# Special thanks

@[floop](https://github.com/flopp)

Translated with www.DeepL.com/Translator (free version)
