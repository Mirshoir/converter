# app.py

import streamlit as st
import os
import tempfile
import pandas as pd
import re
import subprocess

def extract_numbers_and_english(text_content: str):
    pattern = r"\b([A-Za-z]+|\d+)\b"
    return re.findall(pattern, text_content)

def convert_with_gmsh_subprocess(input_stl, output_msh):
    result = subprocess.run(
        ["python", "gmsh_convert.py", input_stl, output_msh],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Gmsh conversion failed:\n{result.stderr}")

def main():
    st.title("STL to Tetrahedral MSH Converter (Fistr-Compatible)")

    uploaded_file = st.file_uploader(
        "Upload a .txt, .asc, .stl, .nas, or .msh file",
        type=["txt", "asc", "stl", "nas", "msh"]
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension in ["txt", "asc", "nas"]:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                extracted = extract_numbers_and_english(file_content)

                if extracted:
                    st.subheader("Extracted Text & Numbers")
                    df_extracted = pd.DataFrame({"Extracted": extracted})
                    st.dataframe(df_extracted)
                else:
                    st.info("No English words or numeric data found.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

        elif file_extension == "stl":
            if st.button("Convert .stl to .msh (Tetrahedral Volume Mesh)"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as temp:
                    temp.write(uploaded_file.getvalue())
                    temp_path = temp.name

                # ✅ Smart file naming
                original_name = uploaded_file.name
                if original_name.endswith("_column_comsol_mesh.stl"):
                    base_name = original_name.replace("_column_comsol_mesh.stl", "")
                    output_name = f"{base_name}Framec_fistr.msh"
                else:
                    output_name = "converted_fistr.msh"  # fallback
                output_path = os.path.join(os.path.dirname(temp_path), output_name)

                try:
                    convert_with_gmsh_subprocess(temp_path, output_path)
                    with open(output_path, "rb") as f_out:
                        st.download_button(
                            label="Download Tetrahedral .msh",
                            data=f_out,
                            file_name=output_name,
                            mime="application/octet-stream"
                        )
                except Exception as ex:
                    st.error(f"Mesh conversion failed: {ex}")
                finally:
                    try:
                        os.remove(temp_path)
                        os.remove(output_path)
                    except:
                        pass

        elif file_extension == "msh":
            st.info("This file is already in .msh format. No conversion needed.")

if __name__ == "__main__":
    main()
