export default function WelcomeBanner() {
  return (
    <section className="rounded-2xl bg-gradient-to-r from-blue-700 to-indigo-700 p-8">

      <h1 className="text-4xl font-bold">
        👋 Welcome back
      </h1>

      <p className="mt-3 text-lg text-blue-100">
        Your autonomous AI has been working for 3 days without human prompts.
      </p>

    </section>
  );
}