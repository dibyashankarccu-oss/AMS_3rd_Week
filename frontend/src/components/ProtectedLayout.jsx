import Sidebar from "./Sidebar";

export default function ProtectedLayout({ children }) {
  return (
    <div className="relative">
      <Sidebar />
      <div className="p-6">{children}</div> {/* removed ml-64 */}
    </div>
  );
}