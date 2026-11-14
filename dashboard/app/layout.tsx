import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'Spotify Review Observatory',description:'Measured review coverage, ranked issues, and traceable evidence.'};
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>}
