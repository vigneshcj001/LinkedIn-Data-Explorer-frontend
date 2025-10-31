# frontend/app.py
import os
import streamlit as st
import requests
import pandas as pd
import altair as alt

# ✅ Use your deployed Railway backend
FASTAPI_URL = os.getenv("FASTAPI_URL", "https://linkedin-data-explorer.onrender.com/api"")

st.set_page_config(page_title="LinkedIn Data Explorer", layout="wide")
st.title("🔗 LinkedIn Data Explorer")
st.write("FastAPI + RapidAPI + Streamlit unified LinkedIn data tool")

# Add all 6 tabs
tabs = st.tabs([
    "🗨️ Post Comments",
    "👤 Profile Details",
    "📰 User Posts",
    "📊 Comment Analytics",
    "🏢 Company Details",
    "📰 Company Posts"
])


def safe_get(d, keys, default=""):
    """Safely extract nested keys from a dictionary"""
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
                try:
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
                except Exception as e:
                    st.error(f"Error fetching comments: {e}")
        else:
            st.warning("Please enter a LinkedIn post URL.")


# TAB 2 – Profile Details
with tabs[1]:
    st.subheader("Fetch Profile Details by Username")
    username = st.text_input("LinkedIn Username:", "vigneshwarancj1")
    if st.button("Get Profile"):
        with st.spinner("Fetching profile..."):
            try:
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
            except Exception as e:
                st.error(f"Error fetching profile: {e}")


# TAB 3 – User Posts
with tabs[2]:
    st.subheader("Fetch Recent Posts by Username")
    username_post = st.text_input("Username:", "vigneshwarancj1")
    if st.button("Get Posts"):
        with st.spinner("Fetching posts..."):
            try:
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
            except Exception as e:
                st.error(f"Error fetching posts: {e}")


# TAB 4 – Comment Analytics
with tabs[3]:
    st.subheader("📊 Analyze LinkedIn Comments")
    post_url = st.text_input("Post URL for analytics:")
    if st.button("Run Analytics"):
        with st.spinner("Analyzing comments..."):
            try:
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
            except Exception as e:
                st.error(f"Error during analytics: {e}")


# TAB 5 – Company Details
with tabs[4]:
    st.subheader("🏢 Fetch Company Details by Identifier")
    identifier = st.text_input("Company Identifier (e.g., youtube, microsoft):", "youtube")
    if st.button("Get Company Info"):
        with st.spinner("Fetching company details..."):
            try:
                res = requests.get(f"{FASTAPI_URL}/company", params={"identifier": identifier})
                data = res.json()
                if not data.get("success"):
                    st.error(data.get("error", "Company data not found"))
                else:
                    info = safe_get(data, ["data", "basic_info"], {})
                    stats = safe_get(data, ["data", "stats"], {})
                    media = safe_get(data, ["data", "media"], {})
                    loc = safe_get(data, ["data", "locations", "headquarters"], {})

                    st.image(media.get("logo_url"), width=150)
                    st.markdown(f"## {info.get('name', '')}")
                    st.write(info.get("description", ""))
                    st.markdown(f"🔗 [{info.get('website', '')}]({info.get('website', '#')})")
                    st.markdown(f"[View on LinkedIn]({info.get('linkedin_url', '#')})")

                    col1, col2 = st.columns(2)
                    col1.metric("👥 Followers", stats.get("follower_count", 0))
                    col2.metric("👔 Employees", stats.get("employee_count", 0))

                    st.markdown("### 📍 Headquarters Location")
                    st.write(f"{loc.get('line1', '')} {loc.get('city', '')} {loc.get('state', '')} {loc.get('country', '')}")

                    st.markdown("### 🏢 Industries")
                    industries = safe_get(info, ["industries"], [])
                    st.write(", ".join(industries) if industries else "No industry info available.")

                    with st.expander("View raw JSON"):
                        st.json(data)
            except Exception as e:
                st.error(f"Error fetching company details: {e}")


# TAB 6 – Company Posts
with tabs[5]:
    st.subheader("📰 Fetch Recent Company Posts")
    company_name = st.text_input("Company Name (e.g., google, microsoft):", "google")
    if st.button("Get Company Posts"):
        with st.spinner("Fetching company posts..."):
            try:
                res = requests.get(f"{FASTAPI_URL}/company/posts", params={"company_name": company_name})
                data = res.json()
                if not data.get("success"):
                    st.error(data.get("error", "No posts found"))
                else:
                    posts = data.get("data", {}).get("posts", [])
                    if not posts:
                        st.warning("No recent posts found for this company.")
                    else:
                        df = pd.DataFrame([{
                            "Date": safe_get(p, ["posted_at", "date"]),
                            "Author": safe_get(p, ["author", "name"]),
                            "Text": (p.get("text", "")[:150] + "..."),
                            "Reactions": safe_get(p, ["stats", "total_reactions"], 0),
                            "Comments": safe_get(p, ["stats", "comments"], 0),
                            "Reposts": safe_get(p, ["stats", "reposts"], 0),
                            "Post URL": p.get("post_url", ""),
                            "Image": safe_get(p, ["media", "items", 0, "url"])
                        } for p in posts])

                        st.dataframe(df, use_container_width=True)

                        st.markdown("### 📊 Post Engagement Overview")
                        chart = alt.Chart(df).mark_bar().encode(
                            x=alt.X("Text:N", title="Post Snippet", sort=None),
                            y=alt.Y("Reactions:Q", title="Total Reactions"),
                            tooltip=["Text", "Reactions", "Comments", "Reposts"]
                        ).properties(width=700, height=400)
                        st.altair_chart(chart, use_container_width=True)

                        st.markdown("### 🖼️ Post Images")
                        for p in posts:
                            image_url = safe_get(p, ["media", "items", 0, "url"])
                            if image_url:
                                st.image(image_url, caption=p.get("author", {}).get("name", ""), use_container_width=True)

                        with st.expander("View raw JSON"):
                            st.json(data)
            except Exception as e:
                st.error(f"Error fetching company posts: {e}")

