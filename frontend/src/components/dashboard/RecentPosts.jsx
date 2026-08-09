const posts = [

    "The Future of AI Agents",

    "Why Developers Need AI",

    "5 LinkedIn Growth Tips"

];

export default function RecentPosts() {

    return (

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">

            <h2 className="text-2xl font-bold mb-6">

                📝 Recent Posts

            </h2>

            <div className="space-y-4">

                {

                    posts.map(post => (

                        <div
                            key={post}
                            className="rounded-xl bg-slate-800 p-4"
                        >

                            {post}

                        </div>

                    ))

                }

            </div>

        </section>

    )

}