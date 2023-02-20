## Github Pages
### 1.为Github Actions添加代码提交权限
访问仓库的 `Settings > Actions > General`页面，找到`Workflow permissions`的设置项，将选项配置为`Read and write permissions`，支持CI将运动数据更新后提交到仓库中。

### 2.提交配置变更代码
1. 更新`./gatsby-config.js`中的`siteMetadata`节点。
```javascript
module.exports = {
  siteMetadata: {
    siteTitle: 'Running Page',
    siteUrl: 'https://tulipsport.github.io/running_page',
    logo: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQTtc69JxHNcmN1ETpMUX4dozAgAN6iPjWalQ&usqp=CAU',
    description: 'Personal site and blog',
    navLinks: [
      {
        name: 'HomePage',
        url: 'http://tulipsport.com',
      },
    ],
  },
}
```
2. 更新Github CI的配置`./.github/workflows/run_data_sync.yml`中的配置为郁金香模式
```yaml
env:
  # please change to your own config.
  RUN_TYPE: tulipsport
  ATHLETE: Runner's Name
  TITLE: Runner Page Title
  MIN_GRID_DISTANCE: 10 # change min distance here
  TITLE_GRID: Over 10km Runs # also here
  GITHUB_NAME: your_github_user_name
  GITHUB_EMAIL: your_github_email
```
3. 在仓库的`Settings > Secrets and variables > Actions`页面添加名为`TULIPSPORT_TOKEN`的新secrets信息，并配置相应token（[如何获取token？](https://tulipsport.rdshoep.com)）

### 3. 手动触发名为`Run Data Sync`的Github Action，同步运动数据并构建gh_pages分支产物。成功后启动仓库的Github Pages功能（页面`Settings > Pages`），操作后等待构建完成即可访问。
具体配置：
- Source： `Deploy from a branch`
- Branch： `gh-pages` && `/(root)`

## Q&A
### 1. 为什么运动数据没有2021年以前的数据？
因郁金香开放平台API接口设计，目前暂时只开放到2021年之后的数据，后期可能会调整，程序将自动支持。（2023/02/24 18:00:00）
