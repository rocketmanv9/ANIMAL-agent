export const metadata = {
  title: 'ANIMAL Command Center',
  description: 'Clawbot operational UI'
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'Inter, system-ui, Arial', background: '#0b1020', color: '#e8ecff' }}>
        {children}
      </body>
    </html>
  );
}
