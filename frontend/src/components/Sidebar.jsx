import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { auth } from "../utils/auth";

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const user = auth.getUser();

  const menu = [
    {
      label: "Search",
      path: "/search",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0015.803 15.803z" />
        </svg>
      ),
    },
    {
      label: "Submit",
      path: "/submit",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: "Dashboard",
      path: "/tickets",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
        </svg>
      ),
    },
    {
      label: "Logs",
      path: "/logs",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
        </svg>
      ),
    },
  ];

  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "U";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

        .ams-sidebar * { font-family: 'DM Sans', sans-serif; }
        .ams-sidebar-brand { font-family: 'Syne', sans-serif; }

        .ams-trigger {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 50;
          height: 60px;
          display: flex;
          align-items: center;
          padding: 0 1.25rem;
          gap: 0.75rem;
          background: linear-gradient(to bottom, rgba(10, 14, 26, 0.98) 0%, rgba(10, 14, 26, 0.85) 100%);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-bottom: 1px solid rgba(139, 92, 246, 0.1);
          box-shadow: 0 1px 20px rgba(0,0,0,0.4);
        }

        .ams-hamburger {
          width: 38px;
          height: 38px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 5px;
          cursor: pointer;
          border-radius: 10px;
          border: 1px solid rgba(139, 92, 246, 0.2);
          background: rgba(139, 92, 246, 0.06);
          transition: all 0.2s ease;
          flex-shrink: 0;
        }
        .ams-hamburger:hover {
          background: rgba(139, 92, 246, 0.15);
          border-color: rgba(139, 92, 246, 0.4);
        }
        .ams-hamburger span {
          display: block;
          width: 18px;
          height: 1.5px;
          background: #a78bfa;
          border-radius: 2px;
          transition: all 0.25s ease;
        }
        .ams-hamburger.open span:nth-child(1) {
          transform: translateY(6.5px) rotate(45deg);
        }
        .ams-hamburger.open span:nth-child(2) {
          opacity: 0;
          transform: scaleX(0);
        }
        .ams-hamburger.open span:nth-child(3) {
          transform: translateY(-6.5px) rotate(-45deg);
        }

        .ams-overlay {
          position: fixed;
          inset: 0;
          top: 60px;
          z-index: 40;
          pointer-events: none;
        }
        .ams-overlay.open {
          pointer-events: auto;
        }

        .ams-backdrop {
          position: absolute;
          inset: 0;
          background: rgba(4, 7, 18, 0.75);
          backdrop-filter: blur(4px);
          -webkit-backdrop-filter: blur(4px);
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        .ams-overlay.open .ams-backdrop {
          opacity: 1;
        }

        .ams-drawer {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 288px;
          background: linear-gradient(160deg, #0d1022 0%, #0a0e1a 50%, #0c0e20 100%);
          border-right: 1px solid rgba(139, 92, 246, 0.12);
          box-shadow: 4px 0 40px rgba(0, 0, 0, 0.6), 1px 0 0 rgba(139, 92, 246, 0.08);
          transform: translateX(-100%);
          transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .ams-overlay.open .ams-drawer {
          transform: translateX(0);
        }

        /* Decorative glow inside drawer */
        .ams-drawer::before {
          content: '';
          position: absolute;
          top: -60px;
          left: -60px;
          width: 220px;
          height: 220px;
          background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
          pointer-events: none;
        }
        .ams-drawer::after {
          content: '';
          position: absolute;
          bottom: 60px;
          right: -40px;
          width: 180px;
          height: 180px;
          background: radial-gradient(circle, rgba(59, 130, 246, 0.06) 0%, transparent 70%);
          pointer-events: none;
        }

        .ams-drawer-inner {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 1.75rem 1.25rem 1.5rem;
        }

        /* User avatar block */
        .ams-avatar {
          width: 46px;
          height: 46px;
          border-radius: 14px;
          background: linear-gradient(135deg, #7c3aed, #2563eb);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          font-size: 1rem;
          color: white;
          flex-shrink: 0;
          box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35);
        }

        .ams-user-block {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          padding: 1rem 1rem;
          background: rgba(139, 92, 246, 0.05);
          border: 1px solid rgba(139, 92, 246, 0.12);
          border-radius: 16px;
          margin-bottom: 1.75rem;
        }

        .ams-user-name {
          font-family: 'Syne', sans-serif;
          font-weight: 600;
          font-size: 0.95rem;
          color: #e2e8f0;
          line-height: 1.2;
        }
        .ams-user-email {
          font-size: 0.72rem;
          color: #64748b;
          margin-top: 2px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 170px;
        }

        /* Section label */
        .ams-section-label {
          font-size: 0.65rem;
          font-weight: 600;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #475569;
          padding: 0 0.5rem;
          margin-bottom: 0.5rem;
        }

        /* Nav items */
        .ams-nav {
          display: flex;
          flex-direction: column;
          gap: 2px;
          flex: 1;
        }

        .ams-nav-item {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          padding: 0.8rem 1rem;
          border-radius: 12px;
          cursor: pointer;
          border: 1px solid transparent;
          transition: all 0.2s ease;
          color: #94a3b8;
          position: relative;
          overflow: hidden;
        }
        .ams-nav-item:hover {
          color: #c4b5fd;
          background: rgba(139, 92, 246, 0.08);
          border-color: rgba(139, 92, 246, 0.15);
        }
        .ams-nav-item.active {
          color: #c4b5fd;
          background: rgba(139, 92, 246, 0.12);
          border-color: rgba(139, 92, 246, 0.25);
        }
        .ams-nav-item.active::before {
          content: '';
          position: absolute;
          left: 0;
          top: 20%;
          bottom: 20%;
          width: 3px;
          background: linear-gradient(to bottom, #7c3aed, #3b82f6);
          border-radius: 0 3px 3px 0;
        }
        .ams-nav-icon {
          flex-shrink: 0;
          opacity: 0.85;
        }
        .ams-nav-label {
          font-size: 0.9rem;
          font-weight: 500;
          letter-spacing: 0.01em;
        }

        /* Divider */
        .ams-divider {
          height: 1px;
          background: linear-gradient(to right, transparent, rgba(139, 92, 246, 0.15), transparent);
          margin: 1.25rem 0;
        }

        /* Logout */
        .ams-logout {
          display: flex;
          align-items: center;
          gap: 0.875rem;
          width: 100%;
          padding: 0.8rem 1rem;
          border-radius: 12px;
          cursor: pointer;
          border: 1px solid rgba(239, 68, 68, 0.15);
          background: rgba(239, 68, 68, 0.05);
          color: #f87171;
          transition: all 0.2s ease;
          font-size: 0.9rem;
          font-weight: 500;
        }
        .ams-logout:hover {
          background: rgba(239, 68, 68, 0.1);
          border-color: rgba(239, 68, 68, 0.3);
          color: #fca5a5;
        }

        /* Version tag */
        .ams-version {
          text-align: center;
          margin-top: 1rem;
          font-size: 0.65rem;
          color: #334155;
          letter-spacing: 0.08em;
        }
          .ams-user-block{
   cursor:pointer;
   transition:all .25s ease;
}

.ams-user-block:hover{
   transform:translateY(-2px);

   background:
   rgba(139,92,246,.08);

   border-color:
   rgba(139,92,246,.3);

   box-shadow:
   0 8px 25px
   rgba(139,92,246,.12);
}
      `}</style>

      <div className="ams-sidebar">
        {/* Spacer to prevent page content from being hidden behind the fixed topbar */}
        <div style={{ height: "60px" }} />

        {/* Top bar — always visible, fixed */}
        <div className="ams-trigger">
          <button
            className={`ams-hamburger ${open ? "open" : ""}`}
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            <span />
            <span />
            <span />
          </button>
          <span className="ams-sidebar-brand" style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: "1.15rem", color: "white", letterSpacing: "-0.01em" }}>
            AMS <span style={{ color: "#a78bfa" }}>Nexus</span>
          </span>
        </div>

        {/* Overlay + Drawer — starts below the topbar */}
        <div className={`ams-overlay ${open ? "open" : ""}`}>
          <div className="ams-backdrop" onClick={() => setOpen(false)} />

          <div className="ams-drawer">
            <div className="ams-drawer-inner">

              {/* User block */}
              <div
                className="ams-user-block"
                onClick={() => {
                  window.open(
                    "/sessions",
                    "_blank"
                  );
                }}
                style={{
                  cursor: "pointer"
                }}
              >

                <div className="ams-avatar">
                  {initials}
                </div>

                <div style={{ overflow: "hidden" }}>

                  <div className="ams-user-name">
                    {user?.name || "User"}
                  </div>

                  <div className="ams-user-email">
                    {user?.email}
                  </div>

                </div>

              </div>

              {/* Nav */}
              <div className="ams-section-label">Navigation</div>
              <nav className="ams-nav">
                {menu.map((m) => {
                  const isActive = location.pathname === m.path;
                  return (
                    <button
                      key={m.path}
                      className={`ams-nav-item ${isActive ? "active" : ""}`}
                      onClick={() => {
                        navigate(m.path);
                        setOpen(false);
                      }}
                    >
                      <span className="ams-nav-icon">{m.icon}</span>
                      <span className="ams-nav-label">{m.label}</span>
                    </button>
                  );
                })}
              </nav>

              {/* Divider */}
              <div className="ams-divider" />

              {/* Logout */}
              <button
                className="ams-logout"
                onClick={() => {
                  auth.logout();
                  navigate("/");
                }}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ flexShrink: 0 }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                </svg>
                Sign Out
              </button>

              <div className="ams-version">AMS NEXUS</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}