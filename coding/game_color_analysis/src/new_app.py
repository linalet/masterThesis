st.subheader("Deep Dive: Style x Decade")
col_decade, col_style = st.columns(2)

with col_decade:
    decade_sel = st.select_slider(
        "Select Decade", options=[1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]
    )

with col_style:
    # Use the full DF for the dropdown options so all styles are represented
    df_decade = df[(df["Year"] >= decade_sel) & (df["Year"] < decade_sel + 10)]
    available_styles = sorted(df_decade["Art_Style"].unique().tolist())
    style_choice = st.selectbox("Art Styles", ["Overall Industry"] + available_styles)

# --- THE MATH LAYER ---
# style_df contains EVERYTHING (including NSFW) for accurate palette calculation
style_df = df_decade.copy()
if style_choice != "Overall Industry":
    style_df = df_decade[df_decade["Art_Style"] == style_choice]

if not style_df.empty:
    # Palette is calculated using the full dataset (Academically accurate)
    palette = helper.get_representative_palette(style_df, count=10)
    p_cols = st.columns(10)
    for i, color in enumerate(palette):
        p_cols[i].markdown(
            f"<div style='background-color:{color}; height:60px; border-radius:5px; border:1px solid #444;'></div>",
            unsafe_allow_html=True,
        )
        p_cols[i].caption(color)

    # --- THE VISUAL LAYER ---
    st.subheader("🖼️ Visual Sample")

    # NEW: Filter the style_df to create a safe pool for images only
    style_df_safe = style_df[style_df["is_nsfw"] == False]

    if not style_df_safe.empty:
        # Pull random samples ONLY from the safe pool
        samples = style_df_safe.sample(min(4, len(style_df_safe)))
        scols = st.columns(4)
        for i, row in enumerate(samples.itertuples()):
            with scols[i % 4]:
                st.image(row.Screenshot, use_container_width=True)
                st.markdown(
                    f"<div style='font-size:14px; text-align:center; color:gray; line-height:1.2; margin-top:5px;'>"
                    f"<b>{row.Game.title()}</b><br>({row.Year})"
                    f"</div>",
                    unsafe_allow_html=True,
                )
    else:
        st.info(
            "🎨 Data is being used for palette calculation, but no 'Safe for Work' screenshots are available to display for this selection."
        )
