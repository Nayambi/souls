import {
  TrendingUp,
  Eye,
  Heart,
  Users,
  BarChart3,
  ArrowUpRight,
} from "lucide-react";

const performance = [
  {
    platform: "LinkedIn",
    reach: "32.8K",
    engagement: "9.4%",
    growth: "+28.6%",
  },
  {
    platform: "X",
    reach: "15.4K",
    engagement: "7.8%",
    growth: "+19.2%",
  },
];

const topPosts = [
  {
    title: "Why AI Agents Are Changing Software Development",
    reach: "12.4K",
    engagement: "8.7%",
  },
  {
    title: "The Future of Autonomous AI",
    reach: "8.9K",
    engagement: "6.4%",
  },
  {
    title: "5 Things Developers Should Know About AI Agents",
    reach: "6.7K",
    engagement: "5.9%",
  },
];

export default function Analytics() {
  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-purple-400">
          PERFORMANCE INTELLIGENCE
        </p>

        <h1 className="text-3xl font-bold text-white md:text-4xl">
          Analytics
        </h1>

        <p className="mt-2 text-slate-400">
          See how your autonomous creator is performing and learning.
        </p>
      </div>

      {/* Main metrics */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="flex items-center justify-between">
            <Eye className="h-5 w-5 text-blue-400" />

            <span className="flex items-center gap-1 text-xs font-semibold text-green-400">
              <ArrowUpRight className="h-3 w-3" />
              24.7%
            </span>
          </div>

          <p className="mt-5 text-sm text-slate-400">
            Total Reach
          </p>

          <p className="mt-1 text-3xl font-bold text-white">
            48.2K
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="flex items-center justify-between">
            <Heart className="h-5 w-5 text-pink-400" />

            <span className="flex items-center gap-1 text-xs font-semibold text-green-400">
              <ArrowUpRight className="h-3 w-3" />
              18.3%
            </span>
          </div>

          <p className="mt-5 text-sm text-slate-400">
            Engagement
          </p>

          <p className="mt-1 text-3xl font-bold text-white">
            8.6%
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="flex items-center justify-between">
            <Users className="h-5 w-5 text-green-400" />

            <span className="flex items-center gap-1 text-xs font-semibold text-green-400">
              <ArrowUpRight className="h-3 w-3" />
              15.8%
            </span>
          </div>

          <p className="mt-5 text-sm text-slate-400">
            Audience Growth
          </p>

          <p className="mt-1 text-3xl font-bold text-white">
            +2.4K
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
          <div className="flex items-center justify-between">
            <TrendingUp className="h-5 w-5 text-purple-400" />

            <span className="flex items-center gap-1 text-xs font-semibold text-green-400">
              <ArrowUpRight className="h-3 w-3" />
              31.2%
            </span>
          </div>

          <p className="mt-5 text-sm text-slate-400">
            Performance Score
          </p>

          <p className="mt-1 text-3xl font-bold text-white">
            92
          </p>
        </div>

      </div>

      {/* Performance overview */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Chart */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 lg:col-span-2">

          <div className="flex items-start justify-between">

            <div>
              <div className="flex items-center gap-3">
                <BarChart3 className="h-5 w-5 text-blue-400" />

                <h2 className="font-semibold text-white">
                  Audience Growth
                </h2>
              </div>

              <p className="mt-1 text-sm text-slate-400">
                Last 30 days
              </p>
            </div>

            <span className="text-sm font-semibold text-green-400">
              +24.7%
            </span>

          </div>

          {/* Fake chart */}
          <div className="mt-8 flex h-56 items-end gap-2">

            {[
              35, 42, 38, 48, 44, 55, 51, 60, 58, 67,
              63, 72, 68, 76, 73, 82, 78, 88, 84, 94,
            ].map((height, index) => (
              <div
                key={index}
                className="flex-1 rounded-t-md bg-blue-500/60 transition hover:bg-blue-400"
                style={{ height: `${height}%` }}
              />
            ))}

          </div>

          <div className="mt-4 flex justify-between text-xs text-slate-600">
            <span>30 days ago</span>
            <span>15 days ago</span>
            <span>Today</span>
          </div>

        </div>

        {/* AI insight */}
        <div className="rounded-2xl border border-purple-500/20 bg-purple-500/5 p-6">

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-500/10">
            <TrendingUp className="h-5 w-5 text-purple-400" />
          </div>

          <h2 className="mt-5 text-lg font-semibold text-white">
            AI Insight
          </h2>

          <p className="mt-3 text-sm leading-7 text-slate-400">
            Your audience responds significantly better to posts about
            autonomous AI and developer tools.
          </p>

          <div className="mt-6 rounded-xl border border-purple-500/20 bg-slate-950/40 p-4">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Recommendation
            </p>

            <p className="mt-2 text-sm font-medium leading-6 text-purple-300">
              Increase AI Agent content by approximately 20%.
            </p>
          </div>

        </div>

      </div>

      {/* Platform performance */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70">

        <div className="border-b border-slate-800 px-6 py-5">
          <h2 className="font-semibold text-white">
            Platform Performance
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Compare how your content performs across platforms.
          </p>
        </div>

        <div className="divide-y divide-slate-800">

          {performance.map((item) => (
            <div
              key={item.platform}
              className="grid gap-4 px-6 py-5 sm:grid-cols-4 sm:items-center"
            >
              <div>
                <p className="font-semibold text-white">
                  {item.platform}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  REACH
                </p>

                <p className="mt-1 font-semibold text-white">
                  {item.reach}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  ENGAGEMENT
                </p>

                <p className="mt-1 font-semibold text-white">
                  {item.engagement}
                </p>
              </div>

              <div>
                <p className="text-xs text-slate-500">
                  GROWTH
                </p>

                <p className="mt-1 font-semibold text-green-400">
                  {item.growth}
                </p>
              </div>
            </div>
          ))}

        </div>

      </div>

      {/* Top content */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70">

        <div className="border-b border-slate-800 px-6 py-5">

          <h2 className="font-semibold text-white">
            Top Performing Content
          </h2>

          <p className="mt-1 text-sm text-slate-400">
            Content that generated the strongest results.
          </p>

        </div>

        <div className="divide-y divide-slate-800">

          {topPosts.map((post, index) => (
            <div
              key={post.title}
              className="flex flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between"
            >

              <div className="flex items-center gap-4">

                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-500/10 text-sm font-bold text-blue-400">
                  #{index + 1}
                </div>

                <p className="font-medium text-white">
                  {post.title}
                </p>

              </div>

              <div className="flex gap-8">

                <div>
                  <p className="text-xs text-slate-500">
                    REACH
                  </p>

                  <p className="mt-1 font-semibold text-white">
                    {post.reach}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    ENGAGEMENT
                  </p>

                  <p className="mt-1 font-semibold text-green-400">
                    {post.engagement}
                  </p>
                </div>

              </div>

            </div>
          ))}

        </div>

      </div>

    </div>
  );
}