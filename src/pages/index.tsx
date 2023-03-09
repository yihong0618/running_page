import Head from 'next/head';
import Image from 'next/image';
import styles from '@/styles/Home.module.css';
import siteMetadata from '../../siteMetadata';

// Note: The subsets need to use single quotes because the font loader values must be explicitly written literal.
// eslint-disable-next-line @typescript-eslint/quotes
interface Props {
  siteMetadata: siteMetadata;
}

export default function Home({siteMetadata}: Props) {
  return (
    <>
      <Head>
        <title>{siteMetadata.siteTitle}</title>
        <meta
          name="description"
          content="TypeScript starter for Next.js that includes all you need to build amazing apps"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <header className={styles.main}>
        <Image
          src={siteMetadata.logo}
          alt="site logo"
          width={150}
          height={100}
        />
        <nav>
          <ul>
            {siteMetadata.navLinks.map((item) => (
              <li key={item.name}>
                <a href={item.url}>{item.name}</a>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main className={styles.main}>
        <div className={styles.leftcolumn}>
          <h1>{siteMetadata.siteTitle}</h1>
          <p>Get started by editing&nbsp;</p>
        </div>
        <div className={styles.rightcolumn}>
          <p>Get started by editing&nbsp;</p>
        </div>
      </main>
    </>
  );
}
