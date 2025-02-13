import Stat from '@/components/Stat';
import useActivities from '@/hooks/useActivities';
import React, { useState } from 'react';



// only support China for now
const CitiesStat = ({ onClick }: { onClick: (_city: string) => void }) => {
  const { cities } = useActivities();

  const citiesArr = Object.entries(cities);
 
  citiesArr.sort((a, b) => b[1] - a[1]);

   // 新增：用于记录当前被点击的城市
   const [clickedCity, setClickedCity] = useState<string | null>(null);
   const handleClick = (cityStr: string) => {
    const city = cityStr.trim();
       // 调用传入的 onClick 函数
       console.log('Before onClick:', city); // 打印点击的城市
       onClick(city);
       console.log('After onClick:', city); // 确认 onClick 调用后的值
       // 更新 clickedCity 状态
       setClickedCity(prev => prev === city ? null : city);
   };


  return (
    <div className="cursor-pointer">
      <h2>路线统计</h2>
      <br></br>
      {/* 显示 clickedCity 的值 */}
      {/* <p>Clicked City: {clickedCity || 'None'}</p> */}
      <section style={{
            maxHeight: '350px', // 设置最大高度为 400px
            overflowY: 'auto',  // 当内容超过最大高度时显示垂直滚动条
            border: '0px solid #ccc', // 为了便于观察，可以添加边框
            padding: '0px' // 添加一些内边距
        }}>
  {citiesArr.map(([city, distance]) => {
    // 移除 "跑点" 两个字
    const processedCity = city.replace("路线", "");

  
    const isClicked = clickedCity!== null && processedCity.startsWith(clickedCity);

    // 新增：判断当前元素是否被点击
    // const isClicked = processedCity === clickedCity;
    // 新增：根据是否被点击设置样式
    const statStyle = {
        // textDecoration: isClicked ? 'underline' : 'none',
        color: isClicked ? 'red' : 'inherit'
    };
    
    return (
     
      <Stat
        key={processedCity}
        value={processedCity}
        description={` ${(distance / 1000).toFixed(0)} KM`}
        citySize={2}
        onClick={() => handleClick(processedCity)}
        style={statStyle} // 新增：应用样式
      />
     
    );
  })}
</section>

     
<div>
        
      </div>
      {/* <hr color="red" /> */}
    </div>
  );
};

export default CitiesStat;
