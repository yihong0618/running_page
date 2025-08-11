// some code from https://github.com/hznulilingbo/igpsride great thanks
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strconv"

	"github.com/go-resty/resty/v2"
)

const (
	GPX_FOLDER = "GPX_OUT"
	TCX_FOLDER = "TCX_OUT"
	FIT_FOLDER = "FIT_OUT"
	BASE_URL   = "https://prod.zh.igpsport.com/service/"
	LOGIN_URL  = BASE_URL + "auth/account/login"
	ACTIVITY_URL = BASE_URL + "web-gateway/web-analyze/activity/"
	QUERY_URL  = ACTIVITY_URL + "queryMyActivity"
	DOWNLOAD_URL = ACTIVITY_URL + "getDownloadUrl/"
)

type iGPSPORT struct {
	client   *resty.Client // http客户端 resty
	userName string        // 用户名
	passWord string        // 密码
	token    string        // token
}

// 创建igpsport对象
func NewIgps(username, password, token string) *iGPSPORT {
	client := resty.New()
	if token != "" {
		client.SetHeader("Authorization", "Bearer "+token)
	}
	return &iGPSPORT{
		client:   client,
		userName: username,
		passWord: password,
		token:    token,
	}
}

type LoginReq struct {
	AppId    string `json:"appId"`
	UserName string `json:"username"`
	PassWord string `json:"password"`
}

type LoginRsp struct {
	Code    int    `json:"Code"`
	Message string `json:"Message"`
	Data    struct {
		TokenType    string `json:"token_type"`
		AccessToken  string `json:"access_token"`
		ExpiresIn    int    `json:"expires_in"`
		RefreshToken string `json:"refresh_token"`
		Scope        string `json:"scope"`
		BoundPhone   bool   `json:"boundPhone"`
	} `json:"data"`
}

// 登录获取token
func (igpsport *iGPSPORT) Login() error {
	if igpsport.userName == "" || igpsport.passWord == "" {
		return errors.New("username or password is empty")
	}
	req := &LoginReq{
		AppId:    "igpsport-web",
		UserName: igpsport.userName,
		PassWord: igpsport.passWord,
	}
	rsp, err := igpsport.client.R().SetHeader("content-type", "application/json").SetBody(req).Post(LOGIN_URL)
	if err != nil {
		return err
	}
	if !rsp.IsSuccess() {
		return errors.New(rsp.Status())
	}
	data := rsp.Body()
	ret := &LoginRsp{}
	if err := json.Unmarshal(data, ret); err != nil {
		return err
	}
	if ret.Data.AccessToken == "" {
		return errors.New("AccessToken nil")
	}
	igpsport.token = ret.Data.AccessToken
	igpsport.client.SetHeader("Authorization", "Bearer "+ret.Data.AccessToken)
	return nil
}

type ActivityItem struct {
	RideId       int    `json:"RideId"`
	MemberId     int    `json:"MemberId"`
	MemberName   string `json:"MemberName"`
	MemberImg    string `json:"MemberImg"`
	Title        string `json:"Title"`
	StartTime    string `json:"StartTime"`
	ThumbPath    string `json:"ThumbPath"`
	RideDistance string `json:"RideDistance"`
	TotalAscent  string `json:"TotalAscent"`
	RecordTime   string `json:"RecordTime"`
	Praise       int    `json:"Praise"`
	IsMy         int    `json:"IsMy"`
	RideTag      string `json:"RideTag"`
	Metric       int    `json:"Metric"`
}

type Row struct {
	Id              string  `json:"id"`
	RideId          int     `json:"rideId"`
	ExerciseType    int     `json:"exerciseType"`
	Title           string  `json:"title"`
	StartTime       string  `json:"startTime"`
	RideDistance    float32 `json:"rideDistance"`
	TotalMovingTime float32 `json:"totalMovingTime"`
	AvgSpeed        float32 `json:"avgSpeed"`
	DataStatus      int     `json:"dataStatus"`
	ErrorType       int     `json:"errorType"`
	AnalysisStatus  int     `json:"analysisStatus"`
	Label           int     `json:"label"`
	IsOpen          int     `json:"isOpen"`
	UnRead          bool    `json:"unRead"`
	Icon            string  `json:"icon"`
}

type GetActivityListRsp struct {
	Message string `json:"message"`
	Code    int    `json:"code"`
	Data    struct {
		PageNo    int   `json:"pageNo"`
		PageSize  int   `json:"pageSize"`
		TotalPage int   `json:"totalPage"`
		TotalRows int   `json:"totalRows"`
		Rows      []Row `json:"rows"`
	} `json:"data"`
}

// 获取活动列表
// reqType 参数："0" fit; "1" gpx; "2" tcx
func (igpsport *iGPSPORT) GetActivityList(pageNo int, ext string) (*GetActivityListRsp, error) {
	if pageNo < 1 {
		return nil, errors.New("pageNo must be greater than 0")
	}

	params := map[string]string{
		"pageNo":   strconv.Itoa(pageNo),
		"pageSize": "20",
		"sort":     "1",
	}
	// 0 fit; 1 gpx; 2 tcx; 3 zip
	switch ext {
	case "fit":
		params["reqType"] = "0"
	case "gpx":
		params["reqType"] = "1"
	case "tcx":
		params["reqType"] = "2"
	default:
		params["reqType"] = "2"
	}
	rsp, err := igpsport.client.SetQueryParams(params).R().Get(QUERY_URL)
	if err != nil {
		return nil, err
	}
	if !rsp.IsSuccess() {
		return nil, errors.New(rsp.Status())
	}
	data := rsp.Body()
	ret := &GetActivityListRsp{}
	if err := json.Unmarshal(data, ret); err != nil {
		return nil, err
	}

	return ret, nil
}

type GetActivityDownLoadUrlRsp struct {
	Message string `json:"message"`
	Code    int    `json:"code"`
	Data    string `json:"data"`
}

// 获取活动下载地址
func (igpsport *iGPSPORT) GetActivityDownLoadUrl(rideId int) (string, error) {
	if rideId == 0 {
		return "", errors.New("rideId is empty")
	}
	rsp, err := igpsport.client.R().Get(DOWNLOAD_URL + strconv.Itoa(rideId))
	if err != nil {
		return "", err
	}
	if !rsp.IsSuccess() {
		return "", errors.New(rsp.Status())
	}
	data := rsp.Body()
	ret := &GetActivityDownLoadUrlRsp{}
	if err := json.Unmarshal(data, ret); err != nil {
		return "", err
	}

	return ret.Data, nil
}

// 通用下载文件函数
func (igpsport *iGPSPORT) downloadFile(urlStr, fileName, ext string) error {
	if urlStr == "" || fileName == "" {
		return errors.New("url or fileName is empty")
	}
	fmt.Println("downloading igpsport", fileName, ext)
	client := resty.New()
	rsp, err := client.R().Get(urlStr)
	if err != nil {
		return err
	}
	if !rsp.IsSuccess() {
		return errors.New(rsp.Status())
	}
	// ensure dir exists
	folder := "TCX_FOLDER"
	switch ext {
	case "fit":
		folder = FIT_FOLDER
	case "gpx":
		folder = GPX_FOLDER
	case "tcx":
		folder = TCX_FOLDER
	default:
		folder = TCX_FOLDER
	}
	if err := os.MkdirAll(folder, 0755); err != nil {
		return err
	}
	filePath := filepath.Join(folder, fileName + "." + ext)
	fWrite, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer fWrite.Close()
	_, err = fWrite.Write(rsp.Body())
	return err
}

// 为特定类型完整下载文件
func (igpsport *iGPSPORT) downloadType(ext string) error {
	if igpsport.token == "" {
		if err := igpsport.Login(); err != nil {
			return err
		}
	}

	page := 1
	for {
		rsp, err := igpsport.GetActivityList(page, ext)
		if err == nil {
			for _, row := range rsp.Data.Rows {
				url, err := igpsport.GetActivityDownLoadUrl(row.RideId)
				if err == nil {
					if err := igpsport.downloadFile(url, strconv.Itoa(row.RideId), ext); err != nil {
						return err
					}
				} else {
					return err
				}
			}
			page++
			if page > rsp.Data.TotalPage {
				break
			}
		} else {
			return err
		}
	}
	return nil
}

func main() {
	username := flag.String("username", "", "igpsport phone number")
	password := flag.String("password", "", "igpsport password")
	token := flag.String("token", "", "from authorization token for download data")
	with_gpx := flag.Bool("with-gpx", false, "get all igpsport data to gpx and download")
	with_tcx := flag.Bool("with-tcx", false, "get all igpsport data to tcx and download")
	with_fit := flag.Bool("with-fit", false, "get all igpsport data to fit and download")
	flag.Parse()

	if *username == "" || *password == "" {
		flag.Usage()
		os.Exit(1)
	}

	// 如果用户没有指定任何下载类型，只下载 tcx
	if !*with_gpx && !*with_tcx && !*with_fit {
		*with_tcx = true
	}

	igpsport := NewIgps(*username, *password, *token)

	// 按用户选择分别下载
	errs := []error{}
	if *with_fit {
		if err := igpsport.downloadType("fit"); err != nil {
			errs = append(errs, fmt.Errorf("fit: %w", err))
		}
	}
	if *with_gpx {
		if err := igpsport.downloadType("gpx"); err != nil {
			errs = append(errs, fmt.Errorf("gpx: %w", err))
		}
	}
	if *with_tcx {
		flag.Usage()
		fmt.Println("type empty or tcx unsupportted yet")
		os.Exit(1)
	}

	if len(errs) > 0 {
		// 打印所有错误并返回非0退出码
		for _, e := range errs {
			fmt.Fprintln(os.Stderr, "error:", e)
		}
		os.Exit(2)
	}

	fmt.Println("done")
}
