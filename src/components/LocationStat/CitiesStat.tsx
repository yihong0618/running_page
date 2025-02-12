import Stat from '@/components/Stat';
import useActivities from '@/hooks/useActivities';

// only support China for now
const CitiesStat = ({ onClick }: { onClick: (_city: string) => void }) => {
  const { cities } = useActivities();

  const citiesArr = Object.entries(cities);
 
  citiesArr.sort((a, b) => b[1] - a[1]);
  return (
    <div className="cursor-pointer">
      {/* <section>
        {citiesArr.map(([city, distance]) => (
          
          <Stat
            key={city}
            value={city}
            description={` ${(distance / 1000).toFixed(0)} KM`}
            citySize={2}
            onClick={() => onClick(city)}
          />
        ))}
      </section> */}

      <section>
  {citiesArr.map(([city, distance]) => {
    // 移除 "跑点" 两个字
    const processedCity = city.replace("路线", "");

    return (
      <Stat
        key={processedCity}
        value={processedCity}
        description={` ${(distance / 1000).toFixed(0)} KM`}
        citySize={2}
        onClick={() => onClick(processedCity)}
      />
    );
  })}
</section>
      <hr color="red" />
    </div>
  );
};

export default CitiesStat;
