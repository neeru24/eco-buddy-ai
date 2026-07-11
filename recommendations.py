def generate_recommendations(
    transport,
    electricity,
    diet,
    flights,
    contributors
):
    recommendations = []
    priority = []

    # Find the biggest contributor
    highest_category = max(contributors, key=contributors.get)

    insight = (
        f"Your biggest contributor is {highest_category} "
        f"({contributors[highest_category]:.0f} kg CO₂/year)."
    )

    # Transport Recommendations

    if transport == "Car":
        priority.append("🚗 Transportation")
        recommendations.append(
            "🚗 Switch to public transport for at least 2–3 days every week."
        )
        recommendations.append(
            "🚶 Walk or cycle for nearby trips under 2 km."
        )

    elif transport == "Public Transport":
        recommendations.append(
            "🚌 Great choice! Continue using public transport whenever possible."
        )

    elif transport == "Bike":
        recommendations.append(
            "🚴 Excellent! Cycling is one of the most eco-friendly transport options."
        )

    elif transport == "Walking":
        recommendations.append(
            "🚶 Walking produces zero carbon emissions. Keep it up!"
        )

    # Electricity Recommendations

    if electricity >= 300:
        priority.append("⚡ Electricity")
        recommendations.append(
            "💡 Your electricity usage is very high. Switch to LED bulbs and energy-efficient appliances."
        )
        recommendations.append(
            "🔌 Turn off unused electronics instead of leaving them on standby."
        )

    elif electricity >= 200:
        recommendations.append(
            "⚡ Try reducing electricity consumption by using appliances efficiently."
        )

    else:
        recommendations.append(
            "🌿 Your electricity usage is already efficient."
        )

    # Diet Recommendations

    if diet == "Non-Vegetarian":
        priority.append("🥩 Diet")
        recommendations.append(
            "🥗 Try replacing 1–2 meat meals every week with plant-based meals."
        )
        recommendations.append(
            "🌱 Plant-based meals can significantly reduce your carbon footprint."
        )

    else:
        recommendations.append(
            "🥬 Great! A vegetarian diet generally has a lower carbon footprint."
        )

    # Flight Recommendations

    if flights >= 5:
        priority.append("✈️ Flights")
        recommendations.append(
            "✈️ Air travel is one of your biggest emission sources. Reduce non-essential flights."
        )
        recommendations.append(
            "🌍 Offset unavoidable flight emissions through verified carbon offset programs."
        )

    elif flights >= 1:
        recommendations.append(
            "🛫 Consider combining trips to reduce the total number of flights."
        )

    else:
        recommendations.append(
            "🌎 Excellent! Your air travel emissions are minimal."
        )

    # Priority Summary

    if priority:
        recommendations.insert(
            0,
            f"🎯 Priority Focus: {', '.join(priority)}"
        )
    else:
        recommendations.insert(
            0,
            "🌱 Excellent! Your lifestyle is already environmentally friendly. Keep maintaining these habits!"
        )

    return insight, recommendations