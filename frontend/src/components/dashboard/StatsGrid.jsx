import StatCard from "./StatCard";

export default function StatsGrid() {

    return (

        <section
            className="
            grid
            gap-6
            md:grid-cols-2
            xl:grid-cols-4
        "
        >

            <StatCard
                title="Posts Generated"
                value="124"
                subtitle="+12 today"
            />

            <StatCard
                title="Followers"
                value="18.4K"
                subtitle="+430"
            />

            <StatCard
                title="Engagement"
                value="92%"
                subtitle="Excellent"
            />

            <StatCard
                title="Ideas Queue"
                value="27"
                subtitle="Ready"
            />

        </section>

    )

}