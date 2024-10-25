import streamlit as st
import numpy as np
import math
from collections import Counter

def read_directions_from_file(file_content, num_dirs, num_t2):
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
            b_vector[idx, 1] = -b_vector[idx, 1]
        elif freq == 'AP':
            b_vector[idx, 1], b_vector[idx, 2] = -b_vector[idx, 2], -b_vector[idx, 1]

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

def main():
    st.title("Tensor File Converter")
    st.write("Upload a tensor file and provide the necessary arguments to convert it.")

    uploaded_file = st.file_uploader("Upload Tensor File", type=["txt", "dat"])
    num_dirs = st.number_input("Number of Directions", min_value=1, step=1)
    b_val = st.number_input("b Value", min_value=0, step=1)
    num_t2 = st.number_input("Number of T2", min_value=0, step=1)
    freq = st.selectbox("Frequency", ["RL", "AP"])
    verbose = st.checkbox("Verbose Output")

    if st.button("Convert"):
        if uploaded_file is not None:
            file_content = uploaded_file.read().decode("utf-8")
            b_vector = read_directions_from_file(file_content, num_dirs, num_t2)
            convert_to_b_vector(b_vector, num_dirs, num_t2, b_val, freq)
            bval_output, bvec_output = display_and_save_b_vector(b_vector, num_dirs, num_t2)

            if verbose:
                st.write("### bval Output:")
                st.write(" ".join(bval_output))

                st.write("### bvec Output:")
                for line in bvec_output:
                    st.write(line)

            st.download_button("Download bval.txt", " ".join(bval_output), "bval.txt")
            st.download_button("Download bvec.txt", "\n".join(bvec_output), "bvec.txt")
        else:
            st.error("Please upload a valid tensor file.")

if __name__ == "__main__":
    main()
