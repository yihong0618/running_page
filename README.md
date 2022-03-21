# [Create a personal workouts home page](http://workouts.ben29.xyz) 

[简体中文](README-CN.md) | English

This project is based on [running_page](https://github.com/yihong0618/running_page), add support for multi sports type. Follow the steps in origin repo to deploy.


## New Features
1. support multi sports type, like Ride/Hike/Swim/Rowing
1. support new apps
    - **[Codoon（咕咚）](#codoon咕咚)** (Couldn't automate for its limitation from server side)
    - **[Xingzhe（行者）](#xingzhe行者)**
1. support [RoadTrip(GoogleMaps)](#roadtripgooglemaps) , show Road Trip in maps



## Custom your page

### Change Sports Color

* Modify Ride Color: `RIDE_COLOR` in `src/utils/const.js` 

### Add Sports Type

* Modify `TYPE_DICT` in  `scripts/config.py`
* Modify `colorFromType` in  `src/utils/util.js` 
---
### Codoon（咕咚）

<details>
<summary>Get your <code>Codoon</code> data</summary>

```python
python3(python) scripts/codoon_sync.py ${your mobile or email} ${your password}
```

example：
```python
python3(python) scripts/codoon_sync.py 13333xxxx xxxx
```

> use `--with-gpx` flag to save your gpx data
>
> use `--from-auth-token` flag to login by refresh_token&user_id

![image](https://user-images.githubusercontent.com/6956444/105690972-9efaab00-5f37-11eb-905c-65a198ad2300.png)

example：

```python
python3(python) scripts/codoon_sync.py 54bxxxxxxx fefxxxxx-xxxx-xxxx --from-auth-token
```

</details>

### Xingzhe（行者）

<details>
<summary>Get your <code>Xingzhe</code> data</summary>

```python
python3(python) scripts/xingzhe_sync.py ${your mobile or email} ${your password}
```

example：
```python
python3(python) scripts/xingzhe_sync.py 13333xxxx xxxx
```

> use `--with-gpx` flag to save your gpx data
>
> use `--from-auth-token` flag to login by refresh_token&user_id

![image](https://user-images.githubusercontent.com/6956444/106879771-87c97380-6716-11eb-9c28-fbf70e15e1c3.png)

example：

```python
python3(python) scripts/xingzhe_sync.py w0xxx 185000 --from-auth-token
```

</details>

### RoadTrip(GoogleMaps)

<details>
<summary>Import KMl from Google Maps</summary>

1. Create map in  [Google Maps](https://www.google.com/maps/d/) (keep route in one Layer)
2. Export Layer to KML file
3. Rename the file to `import.kml` and place it into `scripts`
4. Modify `scripts/kml2polyline.py`, fill in the trip info
  ```
  # TODO modify here
  # trip name
  track.name = "2020-10 Tibet Road Trip"
  # start/end time Year-Month-Day-Hour-Minute
  track.start_time = datetime(2020, 9, 29, 10, 0)
  track.end_time = datetime(2020, 10, 10, 18, 0)
  # total distance
  distance = 4000  # KM
  # total days
  days = 12
  # average daily distacnce
  hours_per_day = 6
  ```
5. Execute in Console
  ```python
  python3(python) scripts\kml2polyline.py
  ```
</details>

# Special thanks
- @[yihong0618](https://github.com/yihong0618) for Awesome [running_page](https://github.com/yihong0618/running_page) , Great Thanks
