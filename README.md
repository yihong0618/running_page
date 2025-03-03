## Release Note

1. Change theme from dark to light, Include Mapbox style and web components style.<br>  暗黑风格转为明亮系风格，个人喜好<br/>
2. Highlight Current selected route and keep other routes background instead of erase them. That inspire me explore more new routes. <br>
  保留并淡化当前地图选择的所有的路线，对当前选择的路线突出显示，从而在平淡枯燥的跑步中能激发探索更多新的路线<br/>
3. Use Routes instead of Cities. Need to Sycn from runalyze.com manually.<br>把城市统计换成了路线统计，因为没去过几个城市，基本生活的城市都占了总运动的95%以上了，缺乏统计乐趣。
<br>需要手动修改data.db数据，或者利用runalyze数据反向同步。我是绕了一个大圈，从华为运动→咕咚（自动同步）→咕咚下载tcx上传Garmin(利用本地服务器自动执行脚本)→Garmin同步Runalyze(网站自动同步)→Runalyze自动导出数据并更新data.db(本地自动执行脚本)
4. Codoon APP will logout when use codoon to sychonize on github<br>咕咚APP手机端会退出，如果用Codoon作为数据源。（咕咚广告太多了，手机APP不用也罢，唯一的作用也就是API开着可以同步华为的数据以及导出数据了）
5. Add scrollbar on main components , e.g. RunTable, LocationStat, YearsStat, that will help read on mobilephone, and locate each run record more smoothly. <br>添加了一些滚动条，这样手机端浏览的时候，就不用滚一长屏了，并且选择RunTable选择某条记录的时候，也可以更方便的在Mapbox中展示，不需要点了之后再滚动到Mapbox进行查看。
6. Download raw data from Codoon, in case one day need to  change my watch from HUAWEI to Garmin.<br>把咕咚运动的原始数据下载下来了 codoon_download.py，这样哪天换运动APP的时候，至少还有自己的历史数据可以供折腾。这可能是跑者最丰富的资产了。有一说一咕咚导出来的数据还算是清晰，相比keep等要解码，Codoon导出来的Json基本可以直接用。
7. Designed a new script named JsontoTcx.py and add more fields in TCX files.<br>把Json转Tcx单独写了个过程，丰富了TCX的字段，加了Distance, Speed, Cadence, Watts等数据，这样佳明Connect 和 佳明Sports里面也可以查看更丰富的图表了
8. Support Teadmill and corrected the wrong elapse time in Garmin Sports when the type is indoor. <br>佳速度这个APP做的比较奇怪，导进去的运动如果是室内跑步（没有轨迹），显示总时间的时候，逻辑是用总时间这个字段减掉全程耗时这个字段，所以经常会出现负时长（因为有停表或者所有Trackpoints加起来时长不等于总时长），导致App统计不准。加了一个DistanceMeter字段和Speed字段后就正常了。
9. Merged get Garmin secret and sycn Garmin App scipts. <br>把获取佳明secret和上传到Garmin Connect的两个过程整合了一下，方便定时任务调用。
10. Add a new button , to change page from yearsStat to CitiesStat quickly. <br>添加了一个按钮，便于快速切换页面到路线统计，原来的彩蛋隐藏得比较深，并且点一下城市，就又跳转回年份统计了。新添加了一个State以标记现在到底点击的是哪个年份，哪个运动或者哪个路线。不至于点了之后纯靠下面的Runtable来判断到底哪个被点击了，尤其手机端浏览时不太方便。
11. Some modifies on Mapbox .<br>修改了Mapbox的部分显示，例如标题中增加了路线字段（如果有），如果是室内跑步没有路线，页面切换到上海市全图。避免每次切换非洲大陆去:) <br>点击某个路线时，如果路线的经纬度跨度特别小（例如跑体育场），那么根据经纬度跨度自动放大比例，避免体育场路线在地图中就显示一个点。
12. Removed some unnecessary components . <br>删除了一些不用的页面元素如logo, SiteMap等。主要还是方便手机浏览的时候少滑动几屏。






## 部署
<p align="Left">
  <a href=https://running-daniel.vercel.app/>Deploy on Vercel</a>
  <br>
  <a href=https://danielyu316.github.io/running_page//>Deploy on Github</a>
  <br>There are data difference between two deployments.As Vercel's Data is run on local server weekly, and Github's Data is run on Github server daily.<br>两个部署的数据源不一样，Vercel是每周在本地服务器上跑一次，然后同步到Git，用的是Keep的数据（已跟咕咚数据去重），Github是每天自动跑一次，用的是咕咚的自动同步。因为咕咚限定了一个账号只能一个地方用。
  <br>Github的数据没法自动更新Route，Vercel的会根据前述的从Runalyze中同步Route再写回到data.db来更新Route.
</p>



## 演示
<p align="center">
  <img src="https://github.com/danielyu316/running_page/blob/master/Running-Daniel.gif?raw=true" alt="demo" width="800">
</p>









