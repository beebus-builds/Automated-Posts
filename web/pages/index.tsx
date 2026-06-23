import type { NextPage } from 'next'
import Head from 'next/head'

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>Match Day</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@700&display=swap" rel="stylesheet" />
      </Head>
      <div id="root">
        <p style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
          Loading Match Day...
        </p>
      </div>
      <script src="/__/firebase/init.js" />
    </>
  )
}

export default Home
