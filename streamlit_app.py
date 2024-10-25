import json
import streamlit as st
import numpy as np
import math
from collections import Counter

def read_JSON_info(json_file):
    # Load JSON data
    json_data = json.load(json_file)
    
    # Default values, which will be overridden if present in JSON
    num_dirs = json_data.get("NumberOfDiffusionDirectionGE", None)
    num_t2 = json_data.get("NumberOfDiffusionT2GE", None)
    phase_encoding_direction = json_data.get("PhaseEncodingDirection", None)

    # Set frequency based on PhaseEncodingDirection or leave as None if not provided
    if phase_encoding_direction in ["j", "j-"]:
        freq = "RL"
    elif phase_encoding_direction in ["i", "i-"]:
        freq = "AP"
    else:
        freq = None  # Frequency not provided in JSON

    return num_dirs, num_t2, freq

def read_directions_from_file(file_content, num_dirs, num_t2):
    num_dirs = num_dirs if num_dirs is not None else 6
    num_t2 = num_t2 if num_t2 is not None else 1

    lines = file_content.splitlines()
    b_vector = np.zeros((num_dirs + num_t2, 4))
    internal_count = 0

    for line in lines:
        tokens = line.split()
        if not tokens:
            continue

        if tokens[0] == str(num_dirs):
            internal_count = 0
            continue

        if len(tokens) > 1 and tokens[0] != "#" and internal_count < num_dirs:
            internal_count += 1
            b_vecx, b_vecy, b_vecz = map(float, tokens[:3])
            b_vector[num_t2 + internal_count - 1, 1:] = [b_vecx, b_vecy, b_vecz]

    return b_vector

def convert_to_b_vector(b_vector, num_dirs, num_t2, b_val, freq):
    for idx in range(num_dirs + num_t2):
        b_vecx, b_vecy, b_vecz = b_vector[idx, 1:]
        b_scale = b_vecx ** 2 + b_vecy ** 2 + b_vecz ** 2
        b_val_new = int((b_val * b_scale + 2.5) / 5) * 5

        b_vector[idx, 0] = b_val_new

        b_vec_scale = math.sqrt(b_val / b_val_new) if b_val_new != 0 else 0
        b_vector[idx, 1:] *= b_vec_scale

    if freq == 'RL':
        b_vector[:, 1] = -b_vector[:, 1]
    elif freq == 'AP':
        b_vector[:, [1, 2]] = -b_vector[:, [2, 1]]

def display_and_save_b_vector(b_vector, num_dirs, num_t2):
    bval_output = [
        ('%.6f' % b_vector[idx, 0]).replace('-0.000000', '0').replace('0.000000', '0')
        for idx in range(num_dirs + num_t2)
    ]
    bvec_output = [
        " ".join([
            ('%.6f' % b_vector[idx, col]).replace('-0.000000', '0').replace('0.000000', '0')
            for idx in range(num_dirs + num_t2)
        ])
        for col in range(1, 4)
    ]
    return bval_output, bvec_output

def initialize_streamlit_components():
    st.title("GE tensor to bval/bvec Converter (beta)")
    st.write("Upload a JSON file to automatically extract the necessary information, or provide the values manually.")

    # File upload options
    uploaded_tensor_file = st.file_uploader("Upload GE tensor file (required*)", type=["txt", "dat"])
    uploaded_json = st.file_uploader("Upload JSON file from dcm2niix (optional)", type=["json"])

    st.image("GEHC_UI.png", caption="Reference Image", use_column_width=True)

    # Set default values in case JSON is not uploaded
    num_dirs, num_t2, freq = 6, 1, "RL"  # Default values

    # Layout changes to put Number of Diffusion Directions and Number of T2 in one line
    col1, col2 = st.columns(2)

    if uploaded_json is not None:
        num_dirs, num_t2, freq = read_JSON_info(uploaded_json)
        with col1:
            if num_dirs is not None:
                st.write(f"Number of Diffusion Directions: <b>{num_dirs}</b> from JSON", unsafe_allow_html=True)
            else:
                num_dirs = st.number_input("Number of Diffusion Directions", min_value=1, step=1, value=6, key='num_dirs')
        
        with col2:
            if num_t2 is not None:
                st.write(f"Number of T2: <b>{num_t2}</b> from JSON", unsafe_allow_html=True)
            else:
                num_t2 = st.number_input("Number of T2", min_value=0, step=1, value=1, key='num_t2')
        
        if freq is not None:
            st.write(f"Frequency: <b>{freq}</b> from JSON", unsafe_allow_html=True)
        else:
            freq = st.radio("Frequency", ["RL", "AP"], key='freq')
    else:
        # Allow users to edit the extracted values or manually input if JSON is not uploaded
        with col1:
            num_dirs = st.number_input("Number of Diffusion Directions", min_value=1, step=1, value=num_dirs, key='num_dirs')
        with col2:
            num_t2 = st.number_input("Number of T2", min_value=0, step=1, value=num_t2, key='num_t2')
        freq = st.radio("Frequency", ["RL", "AP"], index=["RL", "AP"].index(freq), key='freq')

    b_val = st.number_input("b Value", min_value=0, step=1, value=1000, key='b_val')

    return uploaded_tensor_file, num_dirs, num_t2, b_val, freq

def apply_custom_css():
    custom_css = """
        <style>
        .tight-line-spacing {
            line-height: 1.3;
            font-size: 16px;
            margin-bottom: 2px;
            font-family: monospace;
        }
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def main():
    uploaded_tensor_file, num_dirs, num_t2, b_val, freq = initialize_streamlit_components()

    # Process tensor file if uploaded
    if uploaded_tensor_file is not None:
        file_content = uploaded_tensor_file.read().decode("utf-8")
        verbose = st.checkbox("Verbose Output", key='verbose')

        b_vector = read_directions_from_file(file_content, num_dirs, num_t2)
        convert_to_b_vector(b_vector, num_dirs, num_t2, b_val, freq)
        bval_output, bvec_output = display_and_save_b_vector(b_vector, num_dirs, num_t2)

        # Apply custom CSS
        apply_custom_css()

        st.write("### Summary of b-values:")
        b_values = [int(float(b)) for b in bval_output]
        b_counter = Counter(b_values)
        b_summary_html = ""

        for b_value in sorted(b_counter):
            b_summary_html += f"<div class='tight-line-spacing'>b={b_value: >5} x {b_counter[b_value]}</div>"

        st.markdown(b_summary_html, unsafe_allow_html=True)

        if verbose:
            st.write("### bval Output:")
            st.write(" ".join(bval_output))

            st.write("### bvec Output:")
            for line in bvec_output:
                st.write(line)

        file_name_prefix = uploaded_tensor_file.name.split('.')[0]
        download_bval_name = f"{file_name_prefix}_{num_t2}t2_{num_dirs}dir_b{b_val}.bval"
        st.download_button("Download bval file", " ".join(bval_output), download_bval_name, key='download_bval')
        download_bvec_name = f"{file_name_prefix}_{num_t2}t2_{num_dirs}dir_b{b_val}.bvec"
        st.download_button("Download bvec file", "\n".join(bvec_output), download_bvec_name, key='download_bvec')
    else:
        st.error("Please upload a valid tensor file.")

if __name__ == "__main__":
    main()
