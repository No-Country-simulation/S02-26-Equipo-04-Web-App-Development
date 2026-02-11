import { Outlet } from "react-router-dom";

function App() {
  return (
    <main className="min-h-screen text-slate-100">
      <Outlet />
    </main>
  );
}

export default App;
