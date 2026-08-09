export default function AppNavbar() {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950 px-8 flex items-center justify-between">

      <div>

        <h1 className="text-2xl font-bold text-white">
          Autonomous AI Creator
        </h1>

        <p className="text-slate-400 text-sm">
          AI is working autonomously...
        </p>

      </div>

      <div className="flex items-center gap-3">

        <div className="h-3 w-3 rounded-full bg-green-500 animate-pulse"/>

        <span className="text-green-400 font-medium">
          Active
        </span>

      </div>

    </header>
  );
}