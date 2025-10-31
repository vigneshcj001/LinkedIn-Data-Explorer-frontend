# frontend/app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt

FASTAPI_URL = "http://localhost:8000/api"

st.set_page_config(page_title="LinkedIn Data Explorer", layout="wide")
st.title("🔗 LinkedIn Data Explorer")
st.write("FastAPI + RapidAPI + Streamlit unified LinkedIn data tool")

tabs = st.tabs([
    "🗨️ Post Comments",
    "👤 Profile Details",
    "📰 User Posts",
    "📊 Comment Analytics",
    "🏢 Company Details"
])


def safe_get(d, keys, default=""):
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d


# TAB 1 – Post Comments
with tabs[0]:
    st.subheader("Fetch Comments from a LinkedIn Post")
    post_url = st.text_input("Enter LinkedIn Post URL:")
    if st.button("Get Comments"):
        if post_url:
            with st.spinner("Fetching comments..."):
                res = requests.get(f"{FASTAPI_URL}/comments", params={"post_url": post_url})
                data = res.json()
                comments = safe_get(data, ["data", "comments"], [])
                if comments:
                    df = pd.DataFrame([{
                        "Author": safe_get(c, ["author", "name"]),
                        "Comment": c.get("text", ""),
                        "Reactions": safe_get(c, ["stats", "total_reactions"], 0),
                        "Replies": len(c.get("replies", [])),
                        "Date": safe_get(c, ["posted_at", "date"])
                    } for c in comments])
                    st.dataframe(df, use_container_width=True)
                    st.success(f"Fetched {len(comments)} comments.")
                else:
                    st.error("No comments found or invalid URL.")
        else:
            st.warning("Please enter a LinkedIn post URL.")


# TAB 2 – Profile Details
with tabs[1]:
    st.subheader("Fetch Profile Details by Username")
    username = st.text_input("LinkedIn Username:", "vigneshwarancj1")
    if st.button("Get Profile"):
        with st.spinner("Fetching profile..."):
            res = requests.get(f"{FASTAPI_URL}/profile", params={"username": username})
            data = res.json()
            info = safe_get(data, ["data", "basic_info"], {})
            if info:
                st.image(info.get("profile_picture_url"), width=150)
                st.markdown(f"### {info.get('fullname', '')}")
                st.write(info.get("headline", ""))
                st.write(f"📍 {safe_get(info, ['location', 'full'], 'Unknown location')}")
                st.write(f"🔗 [LinkedIn Profile]({info.get('profile_url', '#')})")
            else:
                st.warning("Profile not found.")


# TAB 3 – User Posts
with tabs[2]:
    st.subheader("Fetch Recent Posts by Username")
    username_post = st.text_input("Username:", "vigneshwarancj1")
    if st.button("Get Posts"):
        with st.spinner("Fetching posts..."):
            res = requests.get(f"{FASTAPI_URL}/posts", params={"username": username_post})
            data = res.json()
            posts = safe_get(data, ["data", "posts"], [])
            if posts:
                df = pd.DataFrame([{
                    "Date": safe_get(p, ["posted_at", "date"]),
                    "Text": (p.get("text", "")[:150] + "..."),
                    "Reactions": safe_get(p, ["stats", "total_reactions"], 0),
                    "Comments": safe_get(p, ["stats", "comments"], 0),
                    "URL": p.get("url", "")
                } for p in posts])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No posts found for this user.")


# TAB 4 – Comment Analytics
with tabs[3]:
    st.subheader("📊 Analyze LinkedIn Comments")
    post_url = st.text_input("Post URL for analytics:")
    if st.button("Run Analytics"):
        with st.spinner("Analyzing comments..."):
            res = requests.get(f"{FASTAPI_URL}/analytics/comments", params={"post_url": post_url})
            data = res.json()
            if not data.get("success"):
                st.error(data.get("error", "Failed to analyze comments"))
            else:
                summary = data.get("summary", {})

                col1, col2, col3 = st.columns(3)
                col1.metric("💬 Total Comments", summary.get("total_comments", 0))
                col2.metric("👥 Unique Commenters", summary.get("unique_commenters", 0))
                col3.metric("❤️ Avg. Reactions", round(summary.get("average_reactions", 0), 2))

                st.markdown("### 🔝 Top Commenters by Frequency")
                df_top = pd.DataFrame(summary.get("top_commenters", []), columns=["Author", "Comments"])
                st.dataframe(df_top, use_container_width=True)

                st.markdown("### 📈 Reaction Histogram")
                hist = summary.get("reaction_histogram", {})
                if hist:
                    df_hist = pd.DataFrame(list(hist.items()), columns=["Reactions", "Count"])
                    chart = alt.Chart(df_hist).mark_bar(color="#4C9EE3").encode(
                        x=alt.X("Reactions:Q", title="Number of Reactions per Comment"),
                        y=alt.Y("Count:Q", title="Number of Comments"),
                        tooltip=["Reactions", "Count"]
                    ).properties(width=700, height=400, title="Distribution of Reactions Across Comments")
                    st.altair_chart(chart, use_container_width=True)

                    st.info("""
                    The histogram shows how reactions are distributed across comments.

                    - **X-axis:** How many reactions each comment received  
                    - **Y-axis:** How many comments got that number of reactions  

                    Tall bars on the left → many low-reaction comments.  
                    Tall bars on the right → few high-engagement comments.
                    """)
                else:
                    st.warning("No reaction data available to plot.")


# TAB 5 – Company Details
with tabs[4]:
    st.subheader("🏢 Fetch Company Details by Identifier")
    identifier = st.text_input("Company Identifier (e.g., youtube, microsoft):", "youtube")

    if st.button("Get Company Info"):
        with st.spinner("Fetching company details..."):
            res = requests.get(f"{FASTAPI_URL}/company", params={"identifier": identifier})
            data = res.json()

            if not data.get("success"):
                st.error(data.get("error", "Company data not found"))
            else:
                info = safe_get(data, ["data", "basic_info"], {})
                stats = safe_get(data, ["data", "stats"], {})
                media = safe_get(data, ["data", "media"], {})
                loc = safe_get(data, ["data", "locations", "headquarters"], {})

                # Company branding
                st.image(media.get("logo_url"), width=150)
                st.markdown(f"## {info.get('name', '')}")
                st.write(info.get("description", ""))
                st.markdown(f"🔗 [{info.get('website', '')}]({info.get('website', '#')})")
                st.markdown(f"[View on LinkedIn]({info.get('linkedin_url', '#')})")

                # Company stats
                col1, col2 = st.columns(2)
                col1.metric("👥 Followers", stats.get("follower_count", 0))
                col2.metric("👔 Employees", stats.get("employee_count", 0))

                # Location
                st.markdown("### 📍 Headquarters Location")
                st.write(f"{loc.get('line1', '')} {loc.get('city', '')} {loc.get('state', '')} {loc.get('country', '')}")

                st.markdown("### 🏢 Industries")
                industries = safe_get(info, ["industries"], [])
                if industries:
                    st.write(", ".join(industries))
                else:
                    st.write("No industry info available.")

                # Show raw JSON
                with st.expander("View raw JSON"):
                    st.json(data)
