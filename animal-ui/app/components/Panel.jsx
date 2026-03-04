export default function Panel({ title, children }) {
  return (
    <section style={{ background: '#121a33', border: '1px solid #2a3765', borderRadius: 14, padding: 14 }}>
      <h3 style={{ marginTop: 0, marginBottom: 10, fontSize: 16 }}>{title}</h3>
      {children}
    </section>
  );
}
