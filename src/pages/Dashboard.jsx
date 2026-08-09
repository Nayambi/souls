import {
  Brain,
  TrendingUp,
  FileText,
  Eye,
  Zap,
  Clock,
  ArrowUpRight,
  CheckCircle2,
} from "lucide-react";

const stats = [
  {
    title: "Posts Created",
    value: "24",
    change: "+18.4%",
    icon: FileText,
  },
  {
    title: "Total Reach",
    value: "48.2K",
    change: "+24.7%",
    icon: Eye,
  },
  {
    title: "Engagement",
    value: "8.6%",
    change: "+12.3%",
    icon: TrendingUp,
  },
  {
    title: "Autonomous Actions",
    value: "137",
    change: "+31.2%",
    icon: Zap,
  },
];

const activities = [
  {
    title: "Created LinkedIn post",
    description: "AI Trends in 2026",
    time: "2 min ago",
    status: "Completed",
  },
  {
    title: "Detected trending topic",
    description: "Autonomous AI Agents",
    time: "18 min ago",
    status: "Completed",
  },
  {
    title: "Optimized publishing time",
    description: "Best time: 18:30",
    time: "42 min ago",
    status: "Completed",
  },
  {
    title: "Analyzing audience behavior",
    description: "LinkedIn engagement patterns",
    time: "1 hr ago",
    status: "Running",
  },
];

export default function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <p className="mb-2 text-sm font-medium text-blue-400">
            AUTONOMOUS AI CREATOR
          </p>

          <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Good afternoon 👋
          </h1>

          <p className="mt-2 text-slate-400">
            Your AI is actively creating, learning and optimizing.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/10 px-4 py-2">
          <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
          <span className="text-sm font-medium text-green-400">
            AI is autonomous
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.title}
              className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 transition hover:border-slate-700"
            >
              <div className="flex items-center justify-between">
                <div className="rounded-xl bg-blue-500/10 p-3">
                  <Icon className="h-5 w-5 text-blue-400" />
                </div>

                <span className="text-xs font-medium text-green-400">
                  {stat.change}
                </span>
              </div>

              <p className="mt-5 text-sm text-slate-400">
                {stat.title}
              </p>

              <p className="mt-1 text-3xl font-bold text-white">
                {stat.value}
              </p>
            </div>
          );
        })}
      </div>

      {/* Main grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Autonomous Engine */}
        <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-400" />

                <h2 className="text-lg font-semibold text-white">
                  Autonomous Engine
                </h2>
              </div>

              <p className="mt-1 text-sm text-slate-400">
                What your AI is doing right now
              </p>
            </div>

            <span className="rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400">
              ACTIVE
            </span>
          </div>

          <div className="mt-6 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-5">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Current Goal
              </p>

              <p className="mt-2 text-lg font-semibold text-white">
                Increase LinkedIn engagement
              </p>

              <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800">
                <div className="h-full w-[78%] rounded-full bg-blue-500" />
              </div>

              <div className="mt-2 flex justify-between text-xs text-slate-500">
                <span>Progress</span>
                <span>78%</span>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl bg-slate-950/60 p-4">
                <p className="text-xs text-slate-500">Observed Trend</p>
                <p className="mt-2 font-semibold text-white">
                  AI Agents
                </p>
                <p className="mt-1 text-sm text-green-400">
                  +38%
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-4">
                <p className="text-xs text-slate-500">Decision</p>
                <p className="mt-2 font-semibold text-white">
                  Publish today
                </p>
                <p className="mt-1 text-sm text-blue-400">
                  18:30
                </p>
              </div>

              <div className="rounded-xl bg-slate-950/60 p-4">
                <p className="text-xs text-slate-500">Confidence</p>
                <p className="mt-2 font-semibold text-white">
                  96%
                </p>
                <p className="mt-1 text-sm text-green-400">
                  High confidence
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Next Action */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-yellow-400" />

            <h2 className="text-lg font-semibold text-white">
              Next Action
            </h2>
          </div>

          <div className="mt-6 rounded-xl border border-blue-500/20 bg-blue-500/5 p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Scheduled
            </p>

            <p className="mt-3 text-xl font-bold text-white">
              Publish LinkedIn Post
            </p>

            <p className="mt-2 text-sm text-slate-400">
              AI Agents are changing how teams work.
            </p>

            <div className="mt-5 flex items-center gap-2 text-sm text-blue-400">
              <Clock className="h-4 w-4" />
              Today at 18:30
            </div>

            <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">
              Review Post
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Activity */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Recent Activity
            </h2>

            <p className="mt-1 text-sm text-slate-400">
              Autonomous actions performed by your AI
            </p>
          </div>

          <button className="text-sm font-medium text-blue-400 hover:text-blue-300">
            View all
          </button>
        </div>

        <div className="mt-6 divide-y divide-slate-800">
          {activities.map((activity) => (
            <div
              key={activity.title}
              className="flex items-center gap-4 py-4"
            >
              <div className="rounded-full bg-green-500/10 p-2">
                {activity.status === "Running" ? (
                  <Zap className="h-4 w-4 text-yellow-400" />
                ) : (
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <p className="font-medium text-white">
                  {activity.title}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {activity.description}
                </p>
              </div>

              <div className="text-right">
                <p className="text-xs text-slate-500">
                  {activity.time}
                </p>

                <p
                  className={`mt-1 text-xs ${
                    activity.status === "Running"
                      ? "text-yellow-400"
                      : "text-green-400"
                  }`}
                >
                  {activity.status}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}