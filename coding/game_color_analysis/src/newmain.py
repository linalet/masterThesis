if selected_game_name:
    # 1. FAST LOOKUP: Get all rows for this game (usually 5-10 screenshots)
    # Using .loc is instant because 'Game' is now the index
    game_rows = df.loc[[selected_game_name]]
    main_info = game_rows.iloc[0]

    st.subheader(f"🎨 Color Profile: {selected_game_name.title()}")

    # --- STRIP A: PRE-CALCULATED WEIGHTED DNA ---
    st.markdown("### Global Game DNA (Weighted)")
    dna_string = main_info["Precalc_DNA"]
    if dna_string:
        html_dna = '<div style="display: flex; height: 60px; border-radius: 10px; overflow: hidden; border: 2px solid #333; margin-bottom: 20px;">'
        for entry in dna_string.split("|"):
            color, weight = entry.split(",")
            html_dna += f'<div style="background-color:{color}; flex:{float(weight)};" title="{color}"></div>'
        html_dna += "</div>"
        st.markdown(html_dna, unsafe_allow_html=True)

    # --- STRIP B: MEAN SCREENSHOT PALETTE (Runtime Average) ---
    st.markdown("### Average Screenshot Palette (Mean)")
    game_pal_list = []
    # Only loop through the 8 clusters for the few rows belonging to this game
    for i in range(1, 9):
        r = game_rows[f"C{i}_R"].mean()
        g = game_rows[f"C{i}_G"].mean()
        b = game_rows[f"C{i}_B"].mean()
        if not pd.isna(r):
            game_pal_list.append(f"#{int(r):02x}{int(g):02x}{int(b):02x}")

    if game_pal_list:
        html_mean = '<div style="display: flex; height: 60px; border-radius: 10px; overflow: hidden; border: 2px solid #333;">'
        for color in game_pal_list:
            html_mean += f'<div style="background-color:{color}; flex:1;" title="{color}"></div>'
        html_mean += "</div>"
        st.markdown(html_mean, unsafe_allow_html=True)
