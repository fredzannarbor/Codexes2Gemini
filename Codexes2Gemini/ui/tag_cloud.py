import streamlit as st
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
from streamlit_ui import load_json_file


def load_prompts(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def create_tag_cloud(prompts):
    all_tags = [tag for prompt in prompts.values() for tag in prompt['tags']]
    tag_freq = Counter(all_tags)
    return WordCloud(width=400, height=200, background_color='white').generate_from_frequencies(tag_freq)

def display_tag_cloud(wordcloud, title):
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(title)
    st.pyplot(fig)

def main():
    st.set_page_config(layout="wide", page_title="Prompt Tag Clouds")
    st.title("Prompt Tag Clouds")

    # Load prompts
    user_prompts = load_json_file('user_prompts_dict.json')
    system_prompts = load_json_file('system_instructions.json')

    # Create tag clouds
    user_tag_cloud = create_tag_cloud(user_prompts)
    system_tag_cloud = create_tag_cloud(system_prompts)

    # Display tag clouds
    col1, col2 = st.columns(2)
    with col1:
        display_tag_cloud(user_tag_cloud, "User Prompts Tags")
    with col2:
        display_tag_cloud(system_tag_cloud, "System Prompts Tags")

    # Display prompts with filtering
    st.subheader("Filter Prompts by Tag")
    selected_tag = st.selectbox("Select a tag to filter prompts",
                                sorted(set([tag for prompts in [user_prompts, system_prompts]
                                            for prompt in prompts.values()
                                            for tag in prompt['tags']])))

    if selected_tag:
        st.subheader("User Prompts with selected tag")
        for name, prompt in user_prompts.items():
            if selected_tag in prompt['tags']:
                st.write(f"**{name}**")
                st.write(prompt['prompt'])
                st.write(f"Tags: {', '.join(prompt['tags'])}")
                st.write("---")

        st.subheader("System Prompts with selected tag")
        for name, prompt in system_prompts.items():
            if selected_tag in prompt['tags']:
                st.write(f"**{name}**")
                st.write(prompt['prompt'])
                st.write(f"Tags: {', '.join(prompt['tags'])}")
                st.write("---")

if __name__ == "__main__":
    main()