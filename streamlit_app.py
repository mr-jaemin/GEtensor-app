import json
import streamlit as st
import numpy as np
import math
from collections import Counter
import pandas as pd

def GEtensor_app_help_page():
    st.title("GE Diffusion tensor App Development (beta)")
    st.markdown('''
            ## View/Convert GE tensor to bval/bvec
            by Jaemin Shin, v1.0.20241031

            The **GEtensor-app** is a web-based tool created with Python and Streamlit to facilitate the viewing and conversion of GE diffusion tensor files in a user-friendly format. The app provides an intuitive summary of b-values. It also presents b-vectors in a structured table format, and allows users to convert the data to FSL's bval/bvec format for download.
            
            GE's diffusion gradient directions, including FSL bvec format, are rotation invariant. This means that no matter the scanning           orientation—whether it's double-oblique, straight axial, head-first, or feet-first—the b-vectors stay the same, as long as the          frequency encoding direction doesn’t change.
            
            You may find this app particularly useful if you need:
            - An intuitive display of b-values from a tensor file.
            - Conversion of GE tensor data to FSL bval/bvec format.
            - A case when only a tensor file is available, without access to valid DICOM files.
            ''')
    with st.expander("HOW-TO get the GE tensor file & required scan parameters"):
        st.write("GEHC Diffusion Scan Parameter screen:")
        st.image("GEHC_UI.png", use_column_width=True)
        st.markdown('''
            Locations of GE diffusion tensor files on scanner:
            **- Prior to MR30.0:**
            - All tensor file are saved in `/usr/g/bin`
            
            **- MR30.0 or later:**
            - GE-preloaded tensor files are located in `/srv/nfs/psd/etc`
            - User-provided tensor files should be placed in `/srv/nfs/psd/usr/etc`
            - Precedence is given to the GE directory (`/srv/nfs/psd/etc`) when files with the same name exist in both locations
            
            **JSON sidecar from dcm2niix (v1.0.20220915+):**
            ```json
            {
                ...
                "NumberOfDiffusionDirectionGE": 102,
                "NumberOfDiffusionT2GE": 2,
                "TensorFileNumberGE": 4321,
                "PhaseEncodingDirection": "j",
                ...
                "ConversionSoftware": "dcm2niix",
                "ConversionSoftwareVersion": "v1.0.20230315"
            }
            ''')

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

def read_tensor_file_initial(file_content):
    # Read tensor file content and extract information
    lines = file_content.splitlines()
    num_dirs_list = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Ignore comments and empty lines
        if line and line[0] != '#':
            try:
                # Check if line has a single integer number
                num_dirs = int(line)
                num_dirs_list.append(num_dirs)
                # Skip the number of lines equal to the integer found, plus this line itself
                i += num_dirs + 1
            except ValueError:
                # Return None or an empty list if format is incorrect
                print(f"Invalid format in tensor file at line {i + 1}")
                return None
        else:
            i += 1
    
    return num_dirs_list

def read_directions_from_file(file_content, num_dirs, num_t2):
 #   num_dirs = num_dirs if num_dirs is not None else 6
 #   num_t2 = num_t2 if num_t2 is not None else 1

    lines = file_content.splitlines()
    b_vector = np.zeros((num_dirs + num_t2, 4))
    internal_count = 0
    header_lines = []
    raw_lines = []

    for line in lines:
        tokens = line.split()
        if not tokens:
            continue

        if tokens[0] == str(num_dirs):
            internal_count = 0
            raw_lines = []
            continue

        if line.startswith('#'):
            header_lines.append(line)

        if len(tokens) > 1 and tokens[0] != "#" and internal_count < num_dirs:
            raw_lines.append(line)
            internal_count += 1
            b_vecx, b_vecy, b_vecz = map(float, tokens[:3])
            b_vector[num_t2 + internal_count - 1, 1:] = [b_vecx, b_vecy, b_vecz]

    return b_vector, header_lines, raw_lines

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

def apply_custom_css():
    custom_css = """
        <style>
        .tight-line-spacing {
            line-height: 1.3;
            font-size: 16px;
            margin-bottom: 2px;
            font-family: monospace;
        }
        .header-info {
            font-size: 12px;
            font-family: monospace;
        }
        .raw-lines {
            font-size: 12px;
            font-family: monospace;
        }
        .small-font {
            line-height: 1.0;
            font-size: 13px;
            font-family: monospace;
        }
        </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def main():
    GEtensor_app_help_page()
    apply_custom_css()

    # File upload options
    uploaded_tensor_file = st.file_uploader("Upload GE tensor file (required*)", type=["txt", "dat"])
    uploaded_json = st.file_uploader("(optional) Upload JSON file from dcm2niix to automatically extract the necessary information", type=["json"])

    if uploaded_tensor_file is not None:
        file_content = uploaded_tensor_file.read().decode("utf-8")
        file_name_prefix = uploaded_tensor_file.name.split('.')[0]
        file_name = uploaded_tensor_file.name

        # Read directories list from the file
        num_dirs_list = read_tensor_file_initial(file_content)
        #st.write(f"num_dirs_list: {num_dirs_list}")

        # Conditionally set the initial value of num_dirs based on num_dirs_list
        num_dirs = num_dirs_list[0] 
    
        # Layout changes to put Number of Diffusion Directions and Number of T2 in one line
        col1, col2 = st.columns(2)
    
        if uploaded_json is not None:
            num_dirs_json, num_t2, freq = read_JSON_info(uploaded_json)
            if num_dirs_json is not None:
                num_dirs = num_dirs_json
            with col1:
                if num_dirs is not None:
                    st.write(f"Number of Diffusion Directions: <b>{num_dirs}</b> from JSON", unsafe_allow_html=True)
                else:
                    num_dirs = st.number_input("Number of Diffusion Directions", min_value=6, step=1, value=6, key='num_dirs', disabled=uploaded_tensor_file is None)
            
            with col2:
                if num_t2 is not None:
                    st.write(f"Number of T2: <b>{num_t2}</b> from JSON", unsafe_allow_html=True)
                else:
                    num_t2 = st.number_input("Number of T2", min_value=1, step=1, value=1, key='num_t2')
            
            if freq is not None:
                st.write(f"Frequency: <b>{freq}</b> from JSON", unsafe_allow_html=True)
            else:
                freq = st.radio("Frequency", ["RL", "AP"], key='freq')
        else:
            # Allow users to edit the extracted values or manually input if JSON is not uploaded
            with col1:
                num_dirs = st.selectbox("Number of Diffusion Directions", options=num_dirs_list, index=0)
            with col2:
                num_t2 = st.number_input("Number of T2", min_value=1, step=1, value=1, key='num_t2')
            freq = st.radio("Frequency", ["RL", "AP"], index=["RL", "AP"].index("RL"), key='freq')

        b_val = st.number_input("b-Value", min_value=0, step=1, value=1000, key='b_val')
        
        b_vector, header_lines, raw_lines = read_directions_from_file(file_content, num_dirs, num_t2)
        convert_to_b_vector(b_vector, num_dirs, num_t2, b_val, freq)
        bval_output, bvec_output = display_and_save_b_vector(b_vector, num_dirs, num_t2)

        st.write("### Summary of b-values:")
        b_values = [int(float(b)) for b in bval_output]
        b_counter = Counter(b_values)
        b_summary_html = ""
        for b_value in sorted(b_counter):
            b_summary_html += f"<div class='tight-line-spacing'>b={b_value: >5} x {b_counter[b_value]}</div>"
        st.markdown(b_summary_html, unsafe_allow_html=True)
        with st.expander("Display Header from " + file_name):
            for header_line in header_lines:
                st.markdown(f"<div class='header-info'>{header_line}</div>", unsafe_allow_html=True)
        with st.expander("Display index/bval/bvec as a table"):
            # Create a DataFrame from the b_vector array
            table_data = {
                "b-value": [int(row[0]) for row in b_vector],
                "bvec_x": [float(('%.6f' % row[1]).replace('-0.000000', '0')) for row in b_vector],
                "bvec_y": [float(('%.6f' % row[2]).replace('-0.000000', '0')) for row in b_vector],
                "bvec_z": [float(('%.6f' % row[3]).replace('-0.000000', '0')) for row in b_vector]
            }
            df = pd.DataFrame(table_data, index=range(1, len(b_vector) + 1))
            # Convert the DataFrame to HTML and apply custom CSS
            table_html = df.to_html(classes='small-font', escape=False)
            # Display the table using custom CSS for smaller font size
            st.markdown(table_html, unsafe_allow_html=True)
        with st.expander("Raw Lines from File "+ file_name):
            st.write(num_dirs)
            for raw_line in raw_lines:
                st.markdown(f"<div class='raw-lines'>{raw_line}</div>", unsafe_allow_html=True)
        download_bval_name = f"{file_name_prefix}_{num_t2}t2_{num_dirs}dir_b{b_val}.bval"
        st.download_button("Download bval file", " ".join(bval_output), download_bval_name, key='download_bval')
        download_bvec_name = f"{file_name_prefix}_{num_t2}t2_{num_dirs}dir_b{b_val}.bvec"
        st.download_button("Download bvec file", "\n".join(bvec_output), download_bvec_name, key='download_bvec')
        with st.expander("Display bval/bvec files"):
            st.write("bval Output:")
            st.write(" ".join(bval_output))
            st.write("bvec Output:")
            for line in bvec_output:
                    st.write(line)
    else:
        st.error("Please upload a valid tensor file.")        

if __name__ == "__main__":
    main()
