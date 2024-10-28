# 🎈 GE Diffusion tensor App (beta)
## View/Convert GE tensor to bval/bvec
by Jaemin Shin

The **GEtensor-app** is a web-based tool created with Python and Streamlit to facilitate the viewing and conversion of GE diffusion tensor files in a user-friendly format. The app provides an intuitive summary of b-values, such as:
- b= 0 x 8
- b= 500 x 6
- b= 1000 x 15
- b= 2000 x 15
- b= 3000 x 60

It also presents b-vectors in a structured table format, and allows users to convert the data to FSL's bval/bvec format for download.

GE's diffusion gradient directions, including FSL bvec format, are rotation invariant. This means that no matter the scanning orientation—whether it's double-oblique, straight axial, head-first, or feet-first—the b-vectors stay the same, as long as the frequency encoding direction doesn’t change.

You may find this app particularly useful if you need:
- An intuitive display of b-values from a tensor file.
- Conversion of GE tensor data to FSL bval/bvec format.
- A case when only tensor file id available, without access to valid DICOM files.

## See in action, How to run it
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://getensor.streamlit.app/)

## Screenshots

![image](https://github.com/user-attachments/assets/2fd22493-fc7e-4588-9782-abd4fd064a6c)





### How to run it locally

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
