export default function StatCard({
    title,
    value,
    subtitle
}) {

    return (

        <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6">

            <p className="text-slate-400">
                {title}
            </p>

            <h2 className="text-4xl font-bold mt-3">
                {value}
            </h2>

            <p className="text-green-400 mt-4">
                {subtitle}
            </p>

        </div>

    )

}