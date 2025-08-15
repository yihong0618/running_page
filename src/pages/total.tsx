import ActivityList from '@/components/ActivityList';
import { Helmet } from 'react-helmet-async';

const HomePage = () => {
  return (
    <>
      <Helmet>
        <html lang="en" />
      </Helmet>
      <div className="w-full">
        <ActivityList />
      </div>
    </>
  );
};

export default HomePage;
