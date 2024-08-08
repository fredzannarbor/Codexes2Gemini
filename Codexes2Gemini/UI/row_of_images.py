import streamlit as st
from PIL import Image

# Create a container
with st.container():
    # Set the container height
    st.markdown("""
        <style>
        .fixed-height-container {
            height: 200px;
            overflow-y: hidden;
        }
        .image-container img {
            height: 200px;
            width: auto;
            object-fit: cover;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create a fixed-height container
    with st.container():
        st.markdown('<div class="fixed-height-container">', unsafe_allow_html=True)

        # Create columns for images
        cols = st.columns(4)  # Adjust the number based on how many images you want to display

        # List of image paths
        image_paths = ['image1.jpg', 'image2.jpg', 'image3.jpg', 'image4.jpg']

        # Display images in columns
        for col, image_path in zip(cols, image_paths):
            with col:
                st.markdown(f'<div class="image-container"><img src="data:image/png;base64,{image_to_base64(image_path)}"/></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

