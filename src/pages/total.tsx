import ActivityList from '@/components/ActivityList';
import { Helmet } from 'react-helmet-async';
import { useTheme } from '@/hooks/useTheme';
import { useEffect } from 'react';

const HomePage = () => {
  // Use the theme hook to get the current theme
  const { theme } = useTheme();

  // Apply theme changes to the document when theme changes
  useEffect(() => {
    const htmlElement = document.documentElement;

    if (theme === 'system') {
      // Remove theme attribute to use system preference
      htmlElement.removeAttribute('data-theme');
    } else {
      // Set explicit theme attribute
      htmlElement.setAttribute('data-theme', theme);
    }
  }, [theme]);

  return (
    <>
      <Helmet>
        {/* Set HTML attributes including theme */}
        <html lang="en" data-theme={theme !== 'system' ? theme : undefined} />
      </Helmet>
      <div className="w-full">
        <ActivityList />
      </div>
    </>
  );
};

export default HomePage;
