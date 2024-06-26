import streamlit as st
import tensorflow_hub as hub
import tensorflow as tf
import numpy as np
import PIL
from PIL import Image
import io
import os
# Function to convert tensor to image
def tensor_to_image(tensor):
    tensor = tensor * 255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor) > 3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return PIL.Image.fromarray(tensor)

# Function to load image from file upload
def load_img_from_upload(uploaded_img):
    max_dim = 512
    img = PIL.Image.open(uploaded_img)
    img = np.array(img)
    img = tf.image.convert_image_dtype(img, tf.float32)

    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim

    new_shape = tf.cast(shape * scale, tf.int32)

    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img

# Function to load model
def load_model():
    hub_model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')
    return hub_model

# Function to perform style transfer
def predict(hub_model, content_image, style_image):
    stylized_image = hub_model(tf.constant(content_image), tf.constant(style_image))[0]
    return stylized_image

def main():
    try:
        st.markdown(
            """
            <style>
            .stApp {
                background: linear-gradient(to bottom, #bdc3c7, #99aab5, #6e8496, #2c3e50, #bdc3c7);
                color: #ffffff;
            }

    body {
        background: linear-gradient(to right, #74ebd5, #ACB6E5, #74ebd5);
        color: #2c3e50;
        font-family: Arial, sans-serif;
    }
    .stTitle {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(to bottom right, #4CAF50, #45a049);
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        border: none;
    }
    .stButton>button:hover {
        background: linear-gradient(to bottom right, #45a049, #367c39);
    }
    .stButton>button:active {
        background: linear-gradient(to bottom right, #367c39, #45a049);
    }
    .stFileUploader>div>div>div>label {
        color: #4CAF50;
        font-weight: bold;
    }
    .stFileUploader>div>div>div>div>div {
        background-color: #ffffff;
        border-radius: 8px;
    }
    </style>
    """,
            unsafe_allow_html=True
        )

        st.title("Artistic Style Transfer App")
        # Create three columns
        col1, col2, col3 = st.columns([1, 2, 1])  # Adjust the ratio as needed

        # Load and display an image as a logo in the center column
        logo_path = 'transfer_style_logo.jpg'
        logo = Image.open(logo_path)
        with col2:
            st.image(logo, width=256)

        # Create session state to store model and other variables
        if 'model' not in st.session_state:
            st.session_state.model = load_model()

        if not os.path.exists('stylized_images'):
            os.makedirs('stylized_images')

        st.sidebar.title('Navigation')

        # Sidebar buttons with unique keys for option selection
        if st.sidebar.button('Gallery', key='pred_detail'):
            st.session_state.option = 'Gallery'



        if st.sidebar.button('Upload Images', key='temp_detail'):
            st.session_state.option = 'Upload Images'


        option = st.session_state.get('option', '')


        if option == "Upload Images":
            content_image = st.file_uploader("Upload Content Image", type=['jpg', 'jpeg', 'png'])
            style_image = st.file_uploader("Upload Style Image", type=['jpg', 'jpeg', 'png'])

            if content_image and style_image:
                # Open and resize the uploaded images
                content_img = Image.open(content_image)
                style_img = Image.open(style_image)
                content_img_resized = content_img.resize((256, 256))
                style_img_resized = style_img.resize((256, 256))

                # Display the resized images side by side
                st.subheader("Uploaded Images")
                col1, col2 = st.columns(2)
                with col1:
                    st.image(content_img_resized, caption='Content Image', use_column_width=True)
                with col2:
                    st.image(style_img_resized, caption='Style Image', use_column_width=True)

            if st.button('Transfer Style', key='get_transfer_style'):
                with st.spinner("Applying Style..."):
                    if content_image and style_image:
                        content_img = load_img_from_upload(content_image)
                        style_img = load_img_from_upload(style_image)
                        stylized_image = predict(st.session_state.model, content_img, style_img)

                        # Display the stylized image
                        st.subheader("Stylized Image")
                        st.image(tensor_to_image(stylized_image), caption='Stylized Image', use_column_width=True, output_format="PNG")


                        # Provide a download button for the stylized image
                        img_pil = tensor_to_image(stylized_image)
                        img_pil.save(f"stylized_images/stylized_image_{len(os.listdir('stylized_images')) + 1}.png")

                        img_io = io.BytesIO()
                        img_pil.save(img_io, format='PNG')
                        img_bytes = img_io.getvalue()
                        st.download_button(label="Download Stylized Image", data=img_bytes, file_name="stylized_image.png",
                                           mime="image/png")
                    else:
                        st.warning("Please upload both content and style images.")


        elif option == "Gallery":

            st.subheader("Stylized Images Gallery")

            stylized_images = os.listdir('stylized_images')

            for img_name in stylized_images:
                img_path = os.path.join('stylized_images', img_name)

                st.image(img_path, caption=img_name, use_column_width=True)

    except Exception as e:
        st.error("An error occurred: {}".format(str(e)))

if __name__ == "__main__":
    main()
