"""
charts.py
Generates Plotly charts from PostgreSQL for blog posts.
Run this script to produce HTML files you can embed in your blog.
"""

import psycopg2
import pandas as pd
import plotly.express as px

DB = {
    "host": "127.0.0.1",
    "port": 5433,
    "dbname": "ai_literacy",
    "user": "ailiteracy",
    "password": "ailiteracy",
}


def get_df(query):
    conn = psycopg2.connect(**DB)
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# --- Chart 1: Users by literacy tier ---
df_tiers = get_df("""
    SELECT literacy_tier, COUNT(*) as users
    FROM profiles
    GROUP BY literacy_tier
    ORDER BY literacy_tier
""")
fig1 = px.bar(df_tiers, x="literacy_tier", y="users",
              title="GitHub AI Literacy Distribution (Jan 2026)",
              labels={"literacy_tier": "Tier", "users": "Users"},
              color="literacy_tier")
fig1.write_html("chart_tiers.html")
print("Saved chart_tiers.html")


# --- Chart 2: Top 20 countries by AI developer count ---
df_countries = get_df("""
    SELECT raw_location, COUNT(*) as users
    FROM profiles
    WHERE lat <> 0 AND lon <> 0
      AND raw_location IS NOT NULL AND raw_location != ''
    GROUP BY raw_location
    ORDER BY users DESC
    LIMIT 20
""")
fig2 = px.bar(df_countries, x="users", y="raw_location",
              orientation="h",
              title="Top 20 Locations by AI Developer Count",
              labels={"raw_location": "Location", "users": "Users"})
fig2.update_layout(yaxis={"categoryorder": "total ascending"})
fig2.write_html("chart_top_locations.html")
print("Saved chart_top_locations.html")


# --- Chart 3: World scatter map ---
df_map = get_df("""
    SELECT username, literacy_tier, raw_location, lat, lon, master_ai_literacy_score
    FROM profiles
    WHERE lat <> 0 AND lon <> 0
""")
fig3 = px.scatter_geo(df_map, lat="lat", lon="lon",
                      color="literacy_tier",
                      hover_name="username",
                      hover_data={"raw_location": True, "master_ai_literacy_score": True},
                      title="Global AI Literacy Map (GitHub, Jan 2026)",
                      projection="natural earth")
fig3.write_html("chart_world_map.html")
print("Saved chart_world_map.html")

print("\nAll charts saved. Open the .html files in your browser to view.")
