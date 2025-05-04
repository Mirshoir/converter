import streamlit as st
import re
import os
import tempfile
import meshio
import pandas as pd

def extract_numbers_and_english(text_content: str):
    pattern = r"\b([A-Za-z]+|\d+)\b"
    return re.findall(pattern, text_content)

def degrade_tetra10_to_tetra(input_mesh: meshio.Mesh) -> meshio.Mesh:
    new_cells = []
    for cell_block in input_mesh.cells:
        cell_type, data = cell_block.type, cell_block.data
        if cell_type == "tetra10":
            data = data[:, :4]
            cell_type = "tetra"
        new_cells.append((cell_type, data))
    return meshio.Mesh(
        points=input_mesh.points,
        cells=new_cells,
        point_data=input_mesh.point_data,
        cell_data=input_mesh.cell_data,
        field_data=input_mesh.field_data
    )

def convert_mesh_to_msh(input_path: str, output_path: str):
    mesh = meshio.read(input_path)
    mesh = degrade_tetra10_to_tetra(mesh)
    meshio.write(output_path, mesh)

def main():
    st.title("Mesh & ASCII File Processor")

    uploaded_file = st.file_uploader(
        "Upload a .txt, .asc, .stl, .nas, or .msh file",
        type=["txt", "asc", "stl", "nas", "msh"]
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension in ["txt", "asc", "stl", "nas"]:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                extracted = extract_numbers_and_english(file_content)

                if extracted:
                    st.subheader("Extracted Text & Numbers")
                    df_extracted = pd.DataFrame({"Extracted": extracted})
                    st.dataframe(df_extracted)
                else:
                    st.info("No English words or numeric data found.")

                # Choose which conversion (STL or NAS to MSH)
                if file_extension in ["stl", "nas"]:
                    if st.button(f"Convert .{file_extension} to .msh"):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp:
                            temp.write(uploaded_file.getvalue())
                            temp_path = temp.name

                        output_msh = temp_path.replace(f".{file_extension}", ".msh")

                        try:
                            convert_mesh_to_msh(temp_path, output_msh)
                            with open(output_msh, "rb") as converted_file:
                                st.download_button(
                                    label=f"Download {file_extension}→msh",
                                    data=converted_file,
                                    file_name=os.path.basename(output_msh),
                                    mime="application/octet-stream"
                                )
                        except Exception as ex:
                            st.error(f"Conversion error: {ex}")
                        finally:
                            try:
                                os.remove(temp_path)
                                os.remove(output_msh)
                            except Exception:
                                pass

            except UnicodeDecodeError:
                st.error("Could not decode file content. Please upload an ASCII-based file.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

        elif file_extension == "msh":
            st.info("This file is already in .msh format. No conversion needed.")

if __name__ == "__main__":
    main()
