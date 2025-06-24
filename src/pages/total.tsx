import ActivityList from '@/components/ActivityList';
import { Helmet } from 'react-helmet-async';

const HomePage = () => {
  return (
    <>
      <Helmet>
        <html lang="en" data-theme="dark" />
      </Helmet>
      <div>
        <ActivityList />
      </div>
    </>
  );
};

export default HomePage;
