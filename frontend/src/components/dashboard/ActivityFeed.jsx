const activities = [

    "Searching LinkedIn trends",

    "Ranking ideas",

    "Writing article",

    "Generating image",

    "Scheduling publication"

];

export default function ActivityFeed() {

    return (

        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

            <h2 className="text-2xl font-bold mb-6">

                ⚡ Activity Feed

            </h2>

            <div className="space-y-5">

                {

                    activities.map((activity) => (

                        <div
                            key={activity}
                            className="flex items-center gap-3"
                        >

                            <span className="text-green-400">

                                ✔

                            </span>

                            <span>

                                {activity}

                            </span>

                        </div>

                    ))

                }

            </div>

        </div>

    )

}