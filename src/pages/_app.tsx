import type {AppProps} from 'next/app';
import '@/styles/globals.css';
import siteMetadata from '../../siteMetadata';

export default function App({Component, pageProps}: AppProps) {
  return <Component {...pageProps} siteMetadata={siteMetadata} />;
}
