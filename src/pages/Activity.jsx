import {
  Activity as ActivityIcon,
  FileText,
  Brain,
  Search,
  TrendingUp,
  Clock,
} from "lucide-react";

const activities = [
  {
    icon: FileText,
    title: "Created a new post",
    description: "Why AI Agents Are Changing Software Development",
    time: "2 minutes ago",
    type: "Content",
  },
  {
    icon: Search,
    title: "Discovered a trending topic",
    description: "Autonomous AI agents are becoming mainstream",
    time: "18 minutes ago",
    type: "Discovery",
  },
  {
    icon: Brain,
    title: "Updated content strategy",
    description: "Increased focus on AI Agents and Developer Tools",
    time: "42 minutes ago",
    type: "Learning",
  },
  {
    icon: TrendingUp,
    title: "Optimized posting schedule",
    description: "Best engagement window detected: 10:00 AM",
    time: "1 hour ago",
    type: "Optimization",
  },
  {
    icon: FileText,
    title: "Scheduled a new post",
    description: "5 Things Developers Should Know About AI Agents",
    time: "2 hours ago",
    type: "Content",
  },
];

export default function Activity() {
  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-green-400">
          AUTONOMOUS ENGINE
        </p>

        <h1 className="text-3xl font-bold text-white md:text-4xl">
          Activity
        </h1>

        <p className="mt-2 text-slate-400">
          Everything your AI creator is doing autonomously.
        </p>
      </div>

      {/* Status */}
      <div className="rounded-2xl border border-green-500/20 bg-green-500/5 p-6">

        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

          <div className="flex items-center gap-4">

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/10">
              <ActivityIcon className="h-6 w-6 text-green-400" />
            </div>

            <div>
              <h2 className="font-semibold text-white">
                Autonomous Engine Active
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Your AI is continuously observing, deciding and acting.
              </p>
            </div>

          </div>

          <div className="flex items-center gap-2 text-sm font-semibold text-green-400">
            <span className="h-3 w-3 animate-pulse rounded-full bg-green-400" />
            Running
          </div>

        </div>

      </div>

      {/* Stats */}
      <div className="grid gap-5 md:grid-cols-3">

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-sm text-slate-400">
            Actions Today
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            137
          </p>

          <p className="mt-1 text-sm text-green-400">
            +31.2%
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-sm text-slate-400">
            Decisions Made
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            284
          </p>

          <p className="mt-1 text-sm text-blue-400">
            Autonomous
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <p className="text-sm text-slate-400">
            Last Action
          </p>

          <p className="mt-2 text-3xl font-bold text-white">
            2 min
          </p>

          <p className="mt-1 text-sm text-slate-500">
            ago
          </p>
        </div>

      </div>

      {/* Timeline */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70">

        <div className="border-b border-slate-800 px-6 py-5">

          <div className="flex items-center gap-3">

            <Clock className="h-5 w-5 text-blue-400" />

            <div>
              <h2 className="font-semibold text-white">
                Recent Activity
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Latest autonomous decisions and actions.
              </p>
            </div>

          </div>

        </div>

        <div className="divide-y divide-slate-800">

          {activities.map((activity, index) => {
            const Icon = activity.icon;

            return (
              <div
                key={index}
                className="flex gap-4 px-6 py-5 transition hover:bg-slate-800/30"
              >

                <div className="relative">

                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10">
                    <Icon className="h-5 w-5 text-blue-400" />
                  </div>

                  {index !== activities.length - 1 && (
                    <div className="absolute left-1/2 top-10 h-8 w-px -translate-x-1/2 bg-slate-800" />
                  )}

                </div>

                <div className="min-w-0 flex-1">

                  <div className="flex flex-col justify-between gap-1 sm:flex-row">

                    <h3 className="font-semibold text-white">
                      {activity.title}
                    </h3>

                    <span className="text-xs text-slate-500">
                      {activity.time}
                    </span>

                  </div>

                  <p className="mt-1 text-sm text-slate-400">
                    {activity.description}
                  </p>

                  <span className="mt-3 inline-block rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
                    {activity.type}
                  </span>

                </div>

              </div>
            );
          })}

        </div>

      </div>

      {/* Bottom message */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

        <div className="flex items-start gap-4">

          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-purple-500/10">
            <Brain className="h-5 w-5 text-purple-400" />
          </div>

          <div>
            <h3 className="font-semibold text-white">
              The AI doesn't wait for instructions.
            </h3>

            <p className="mt-1 text-sm leading-6 text-slate-400">
              It observes trends, evaluates opportunities, creates content,
              learns from results and continuously adjusts its strategy.
            </p>
          </div>

        </div>

      </div>

    </div>
  );
}