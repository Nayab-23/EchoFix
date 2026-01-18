import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'EchoFix - Reddit to Engineering Pipeline',
  description: 'Track Reddit feedback through automated engineering workflow',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  )
}
