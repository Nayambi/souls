import {
  Settings as SettingsIcon,
  Bot,
  Bell,
  Shield,
  Zap,
  Save,
} from "lucide-react";

export default function Settings() {
  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-slate-400">
          SYSTEM CONFIGURATION
        </p>

        <h1 className="text-3xl font-bold text-white md:text-4xl">
          Settings
        </h1>

        <p className="mt-2 text-slate-400">
          Configure how your autonomous AI operates.
        </p>
      </div>

      {/* Autonomous Engine */}
      <div className="rounded-2xl border border-green-500/20 bg-green-500/5 p-6">

        <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">

          <div className="flex items-center gap-4">

            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-green-500/10">
              <Bot className="h-6 w-6 text-green-400" />
            </div>

            <div>
              <h2 className="font-semibold text-white">
                Autonomous Mode
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Allow the AI to make decisions without manual approval.
              </p>
            </div>

          </div>

          <div className="flex items-center gap-3">

            <span className="text-sm font-medium text-green-400">
              Active
            </span>

            <div className="flex h-7 w-12 items-center rounded-full bg-green-500 p-1">
              <div className="ml-auto h-5 w-5 rounded-full bg-white shadow" />
            </div>

          </div>

        </div>

      </div>

      {/* Settings sections */}
      <div className="grid gap-6 lg:grid-cols-2">

        {/* AI Behaviour */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

          <div className="flex items-center gap-3">

            <Zap className="h-5 w-5 text-yellow-400" />

            <div>
              <h2 className="font-semibold text-white">
                AI Behaviour
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Control autonomous decision-making.
              </p>
            </div>

          </div>

          <div className="mt-6 space-y-5">

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  Discover trending topics
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Automatically search for relevant conversations.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  Generate content
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Create posts when an opportunity is detected.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  Optimize strategy
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Learn from performance and adjust future actions.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

          </div>

        </div>

        {/* Notifications */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

          <div className="flex items-center gap-3">

            <Bell className="h-5 w-5 text-blue-400" />

            <div>
              <h2 className="font-semibold text-white">
                Notifications
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Decide what the AI should report.
              </p>
            </div>

          </div>

          <div className="mt-6 space-y-5">

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  Important decisions
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Notify when the AI makes a major decision.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  New posts
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Receive updates when content is published.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

            <label className="flex items-center justify-between gap-4">

              <div>
                <p className="text-sm font-medium text-white">
                  Weekly reports
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Receive a summary of AI performance.
                </p>
              </div>

              <input
                type="checkbox"
                defaultChecked
                className="h-5 w-5 accent-blue-600"
              />

            </label>

          </div>

        </div>

        {/* Safety */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

          <div className="flex items-center gap-3">

            <Shield className="h-5 w-5 text-purple-400" />

            <div>
              <h2 className="font-semibold text-white">
                Safety & Control
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                Keep important actions under control.
              </p>
            </div>

          </div>

          <div className="mt-6 space-y-5">

            <div>
              <label className="text-sm font-medium text-slate-300">
                Autonomy Level
              </label>

              <select
                defaultValue="high"
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              >
                <option value="low">
                  Low — Ask before important actions
                </option>

                <option value="medium">
                  Medium — Autonomous with limits
                </option>

                <option value="high">
                  High — Fully autonomous
                </option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-300">
                Daily Action Limit
              </label>

              <input
                type="number"
                defaultValue="200"
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              />
            </div>

          </div>

        </div>

        {/* System */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

          <div className="flex items-center gap-3">

            <SettingsIcon className="h-5 w-5 text-slate-300" />

            <div>
              <h2 className="font-semibold text-white">
                System
              </h2>

              <p className="mt-1 text-sm text-slate-400">
                General system preferences.
              </p>
            </div>

          </div>

          <div className="mt-6 space-y-5">

            <div>
              <label className="text-sm font-medium text-slate-300">
                Operating Mode
              </label>

              <select
                defaultValue="continuous"
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              >
                <option value="continuous">
                  Continuous
                </option>

                <option value="scheduled">
                  Scheduled
                </option>

                <option value="manual">
                  Manual
                </option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-300">
                Timezone
              </label>

              <select
                defaultValue="Africa/Maputo"
                className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              >
                <option value="Africa/Maputo">
                  Africa / Maputo
                </option>

                <option value="UTC">
                  UTC
                </option>

                <option value="America/New_York">
                  America / New York
                </option>
              </select>
            </div>

          </div>

        </div>

      </div>

      {/* Save */}
      <div className="flex justify-end border-t border-slate-800 pt-6">

        <button className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-semibold text-white transition hover:bg-blue-500">
          <Save className="h-4 w-4" />
          Save Settings
        </button>

      </div>

    </div>
  );
}