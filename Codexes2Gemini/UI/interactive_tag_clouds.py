import streamlit as st
import json
from collections import Counter
import random


from streamlit_ui import load_json_file


def create_tag_frequencies(prompts):
    all_tags = [tag for prompt in prompts.values() for tag in prompt['tags']]
    return Counter(all_tags)


def display_interactive_tag_cloud(tag_freq, title, key_prefix):
    st.subheader(title)

    # Normalize tag frequencies
    max_freq = max(tag_freq.values())
    min_freq = min(tag_freq.values())

    # Create columns for tags
    cols = st.columns(4)

    tag_cloud_html = ""
    for i, (tag, freq) in enumerate(sorted(tag_freq.items())):
        # Normalize font size between 1 and 3 based on frequency
        font_size = 1 + (freq - min_freq) / (max_freq - min_freq) * 2
        color = f"rgb({random.randint(100, 200)}, {random.randint(100, 200)}, {random.randint(100, 200)})"

        # Create a clickable tag using HTML
        tag_html = f'<a href="#{key_prefix}_{tag}" style="font-size: {font_size}em; color: {color}; text-decoration: none;">{tag}</a>&nbsp;'
        tag_cloud_html += tag_html

        # Start a new line every 4 tags
        if (i + 1) % 4 == 0:
            tag_cloud_html += "<br>"

    # Display the entire tag cloud
    st.markdown(tag_cloud_html, unsafe_allow_html=True)

    # Check if a tag was clicked
    clicked_tag = st.query_params.get(key_prefix, [None])[0]
    if clicked_tag:
        st.query_params(**{key_prefix: clicked_tag})
        return clicked_tag
    return None


def display_filtered_prompts(prompts, tag):
    for name, prompt in prompts.items():
        if tag in prompt['tags']:
            st.write(f"**{name}**")
            st.write(prompt['prompt'])
            st.write(f"Tags: {', '.join(prompt['tags'])}")
            st.write("---")


def main():
    st.set_page_config(layout="wide", page_title="Interactive Prompt Tag Clouds")
    st.title("Interactive Prompt Tag Clouds")

    # Load prompts
    user_prompts = load_json_file('user_prompts_dict.json')
    system_prompts = load_json_file('system_instructions.json')

    # Create tag frequencies
    user_tag_freq = create_tag_frequencies(user_prompts)
    system_tag_freq = create_tag_frequencies(system_prompts)

    # Display interactive tag clouds
    col1, col2 = st.columns(2)
    with col1:
        selected_user_tag = display_interactive_tag_cloud(user_tag_freq, "User Prompts Tags", "user")
    with col2:
        selected_system_tag = display_interactive_tag_cloud(system_tag_freq, "System Prompts Tags", "system")

    # Display prompts based on selected tag
    if selected_user_tag:
        st.subheader(f"User Prompts with tag: {selected_user_tag}")
        display_filtered_prompts(user_prompts, selected_user_tag)

    if selected_system_tag:
        st.subheader(f"System Prompts with tag: {selected_system_tag}")
        display_filtered_prompts(system_prompts, selected_system_tag)


if __name__ == "__main__":
    main()