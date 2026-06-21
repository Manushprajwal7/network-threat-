import Sidebar from '../../components/Sidebar';
import TopNavbar from '../../components/TopNavbar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen relative hex-grid" style={{ background: 'var(--bg-void)' }}>
      <div className="fixed inset-0 pointer-events-none z-0">
        <div style={{
          position: 'absolute', top: '15%', left: '30%', width: 600, height: 400,
          background: 'radial-gradient(ellipse, rgba(0,212,255,0.04) 0%, transparent 70%)',
          transform: 'translate(-50%,-50%)',
        }} />
        <div style={{
          position: 'absolute', top: '70%', right: '10%', width: 400, height: 300,
          background: 'radial-gradient(ellipse, rgba(191,95,255,0.035) 0%, transparent 70%)',
        }} />
      </div>
      <Sidebar />
      <TopNavbar />
      <main id="main-content" className="relative z-10 transition-all duration-300"
        style={{ marginLeft: 240, marginTop: 56, padding: '24px', minHeight: 'calc(100vh - 56px)' }}>
        {children}
      </main>
    </div>
  );
}
