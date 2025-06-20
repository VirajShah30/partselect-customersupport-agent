import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Part Select Customer Support Agent',
  description: 'Created by Viraj Shah'
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
