import { NavLink } from "react-router-dom";

const links = [
  ["Dashboard", "/dashboard"],
  ["Persona", "/persona"],
  ["Posts", "/posts"],
  ["Activity", "/activity"],
  ["Analytics", "/analytics"],
  ["Settings", "/settings"],
];

export default function Sidebar() {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900 p-6">
      <h1 className="mb-10 text-2xl font-bold text-blue-500">
        🤖 Autonomous AI
      </h1>

      <nav className="space-y-3">
        {links.map(([title, url]) => (
          <NavLink
            key={url}
            to={url}
            className={({ isActive }) =>
              `block rounded-lg px-4 py-3 transition ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            {title}
          </NavLink>
        ))}
      </nav>

      <div className="mt-10 rounded-xl bg-slate-800 p-4">
        <p className="font-semibold text-green-400">
          🟢 AI Active
        </p>

        <p className="mt-2 text-sm text-slate-400">
          Running autonomously
        </p>
      </div>
    </aside>
  );
}