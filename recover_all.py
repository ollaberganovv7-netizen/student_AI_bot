import os

filepaths = [r"handlers\documents.py", r"handlers\presentation.py"]

for filepath in filepaths:
    with open(filepath, "r", encoding="utf-8") as f:
        s = f.read()
    
    # Check if the file is corrupted (has a space at index 0 and BOM at index 1)
    if s.startswith(" \ufeff"):
        recovered = s[1::2]
        
        # Remove the BOM if it got carried over
        recovered = recovered.lstrip("\ufeff")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(recovered)
        print(f"Recovered {filepath}!")
    else:
        print(f"File {filepath} doesn't seem corrupted in this specific way.")
