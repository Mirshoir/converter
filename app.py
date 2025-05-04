import streamlit as st
import re
import os
import tempfile
import meshio
import pandas as pd

def extract_numbers_and_english(text_content: str):
    """
    Extract English words and numbers from the given string.
    
    :param text_content: A string representing the ASCII content of the uploaded file.
    :return: A list of extracted words/numbers.
    """
    pattern = r"\b([A-Za-z]+|\d+)\b"
    return re.findall(pattern, text_content)

def degrade_tetra10_to_tetra(input_mesh: meshio.Mesh) -> meshio.Mesh:
    """
    Degrade any second-order tetrahedral elements (tetra10) to first-order tetrahedra (tetra).
    
    :param input_mesh: The meshio.Mesh object that may contain tetra10 elements.
    :return: The modified meshio.Mesh object with tetra10 degraded to tetra.
    """
    new_cells = []
    for cell_block in input_mesh.cells:
        cell_type, data = cell_block.type, cell_block.data
        # If it's a tetra10, we keep only the first 4 corner nodes
        if cell_type == "tetra10":
            data = data[:, :4]
            cell_type = "tetra"
        new_cells.append((cell_type, data))

    degraded_mesh = meshio.Mesh(
        points=input_mesh.points,
        cells=new_cells,
        point_data=input_mesh.point_data,
        cell_data=input_mesh.cell_data,
        field_data=input_mesh.field_data
    )
    return degraded_mesh

def convert_to_msh(file_path: str, output_path: str):
    """
    Read an STL/NAS mesh file and convert it to MSH format, degrading tetra10 to tetra4 if needed.
    
    :param file_path: Path to the input STL/NAS file.
    :param output_path: Path to save the resulting .msh file.
    """
    mesh = meshio.read(file_path)
    mesh = degrade_tetra10_to_tetra(mesh)
    meshio.write(output_path, mesh)

def main():
    """
    Main Streamlit application that lets users upload a file, extracts ASCII data if relevant,
    and optionally converts STL/NAS to MSH format.
    """
    st.title("Mesh & ASCII File Processor")

    uploaded_file = st.file_uploader(
        "Upload a .txt, .asc, .stl, .nas, or .msh file",
        type=["txt", "asc", "stl", "nas", "msh"]
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()

        # For ASCII readable formats, attempt to extract text content
        if file_extension in ["txt", "asc", "stl", "nas"]:
            try:
                file_content = uploaded_file.read().decode("utf-8")
                
                # Extract English words and numbers
                extracted = extract_numbers_and_english(file_content)
                
                if extracted:
                    # Present extracted data in a DataFrame
                    st.subheader("Extracted Text & Numbers")
                    df_extracted = pd.DataFrame({"Extracted": extracted})
                    st.dataframe(df_extracted)
                else:
                    st.info("No words or numeric data found.")

                # If a file is .stl or .nas, allow conversion to .msh
                if file_extension in ["stl", "nas"]:
                    if st.button("Convert to .msh"):
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=f".{file_extension}"
                        ) as temp:
                            temp.write(uploaded_file.getvalue())
                            temp_path = temp.name

                        # Define the output .msh path
                        output_msh = temp_path.replace(f".{file_extension}", ".msh")
                        
                        try:
                            convert_to_msh(temp_path, output_msh)

                            # Read back the .msh file for download
                            with open(output_msh, "rb") as converted_file:
                                st.download_button(
                                    label="Download .msh",
                                    data=converted_file,
                                    file_name=os.path.basename(output_msh),
                                    mime="application/octet-stream"
                                )
                        except Exception as ex:
                            st.error(f"Conversion error: {ex}")
                        finally:
                            # Clean up any temp files
                            try:
                                os.remove(temp_path)
                                os.remove(output_msh)
                            except Exception:
                                pass

            except UnicodeDecodeError:
                st.error("Could not decode the file content. Please upload an ASCII-based file.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

        # If a file is already .msh, show an info message
        elif file_extension == "msh":
            st.info("This file is already in .msh format. No extraction or conversion needed.")

if __name__ == "__main__":
    main()