import ActivityList from '../components/ActivityList';
import { Helmet } from 'react-helmet-async';
import { useTheme } from '../hooks/useTheme';

const SummaryPage = () => {
  const { theme } = useTheme();
  return (
    <>
      <Helmet>
        <html data-theme={theme} />
      </Helmet>
      <ActivityList />
    </>
  );
};

export default SummaryPage;
