# scratch/inspect_json.py
import json

file_path = "db/stories/hsk-1/first-plane-trip/chapter-1-the-taxi-arrives-late.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

with open("scratch/json_inspect_result.txt", "w", encoding="utf-8") as out:
    out.write("Keys in JSON: " + str(list(data.keys())) + "\n")
    for k in data.keys():
        val = data[k]
        if isinstance(val, (list, dict)):
            out.write(f"  {k}: type={type(val)}, len={len(val)}\n")
            if len(val) > 0:
                # Write a sample item
                if isinstance(val, dict):
                    sample_k = list(val.keys())[0]
                    out.write(f"    Sample: {sample_k} -> {val[sample_k]}\n")
                elif isinstance(val, list):
                    out.write(f"    Sample: {val[0]}\n")
        else:
            out.write(f"  {k}: type={type(val)}, val={str(val)[:100]}\n")
            
print("Wrote inspection results to scratch/json_inspect_result.txt")
