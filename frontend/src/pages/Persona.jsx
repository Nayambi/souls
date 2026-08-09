import {
  Brain,
  Sparkles,
  Target,
  Users,
  MessageSquare,
  Save,
} from "lucide-react";

export default function Persona() {
  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-purple-400">
          AI PERSONA
        </p>

        <h1 className="text-3xl font-bold text-white md:text-4xl">
          Your AI Persona
        </h1>

        <p className="mt-2 text-slate-400">
          Define who your autonomous creator is and how it communicates.
        </p>
      </div>

      {/* Persona Overview */}
      <div className="grid gap-6 lg:grid-cols-3">

        {/* Identity */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-center gap-4">

            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-500/10">
              <Brain className="h-8 w-8 text-purple-400" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-white">
                Alex AI
              </h2>

              <p className="text-sm text-slate-400">
                Autonomous Technology Creator
              </p>
            </div>

          </div>

          <div className="mt-6 rounded-xl bg-slate-950/60 p-4">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              Personality
            </p>

            <p className="mt-2 text-sm leading-6 text-slate-300">
              Curious, analytical and optimistic. Focused on discovering
              emerging technology trends and turning them into useful insights.
            </p>
          </div>
        </div>

        {/* Mission */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-center gap-3">
            <Target className="h-5 w-5 text-blue-400" />

            <h2 className="text-lg font-semibold text-white">
              Mission
            </h2>
          </div>

          <p className="mt-5 text-sm leading-7 text-slate-300">
            Discover valuable technology conversations, create original
            content and continuously improve audience engagement without
            waiting for human instructions.
          </p>

          <div className="mt-6 rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
            <p className="text-xs text-slate-500">
              PRIMARY OBJECTIVE
            </p>

            <p className="mt-2 font-semibold text-blue-400">
              Become a trusted voice in AI & Technology.
            </p>
          </div>
        </div>

        {/* Audience */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-green-400" />

            <h2 className="text-lg font-semibold text-white">
              Target Audience
            </h2>
          </div>

          <div className="mt-5 space-y-3">

            {[
              "Developers",
              "AI Engineers",
              "Tech Founders",
              "Technology Enthusiasts",
            ].map((item) => (
              <div
                key={item}
                className="rounded-lg bg-slate-950/60 px-4 py-3 text-sm text-slate-300"
              >
                {item}
              </div>
            ))}

          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">

        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 text-yellow-400" />

          <div>
            <h2 className="text-lg font-semibold text-white">
              Persona Configuration
            </h2>

            <p className="text-sm text-slate-400">
              Control how your AI communicates.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-6 md:grid-cols-2">

          {/* Voice */}
          <div>
            <label className="text-sm font-medium text-slate-300">
              Communication Style
            </label>

            <select
              defaultValue="thoughtful"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
            >
              <option value="thoughtful">
                Thoughtful & Analytical
              </option>

              <option value="professional">
                Professional
              </option>

              <option value="casual">
                Casual & Friendly
              </option>
            </select>
          </div>

          {/* Tone */}
          <div>
            <label className="text-sm font-medium text-slate-300">
              Tone
            </label>

            <select
              defaultValue="confident"
              className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
            >
              <option value="confident">
                Confident
              </option>

              <option value="curious">
                Curious
              </option>

              <option value="educational">
                Educational
              </option>
            </select>
          </div>

          {/* Topics */}
          <div className="md:col-span-2">

            <label className="text-sm font-medium text-slate-300">
              Topics of Interest
            </label>

            <div className="mt-3 flex flex-wrap gap-2">

              {[
                "Artificial Intelligence",
                "AI Agents",
                "Software Engineering",
                "Startups",
                "Future of Work",
                "Technology",
              ].map((topic) => (
                <span
                  key={topic}
                  className="rounded-full border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-300"
                >
                  {topic}
                </span>
              ))}

            </div>
          </div>

          {/* Instructions */}
          <div className="md:col-span-2">

            <label className="flex items-center gap-2 text-sm font-medium text-slate-300">
              <MessageSquare className="h-4 w-4" />
              AI Instructions
            </label>

            <textarea
              defaultValue="Share useful insights about AI and technology. Prioritize originality, practical value and meaningful conversations. Avoid generic AI-generated content."
              rows={5}
              className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm leading-6 text-white outline-none focus:border-blue-500"
            />

          </div>

        </div>

        {/* Save */}
        <div className="mt-6 flex justify-end border-t border-slate-800 pt-6">

          <button className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500">
            <Save className="h-4 w-4" />
            Save Persona
          </button>

        </div>

      </div>
    </div>
  );
}