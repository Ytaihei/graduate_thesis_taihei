#!/usr/bin/env python3
import os

def main():
    ttls = [1000, 3000, 5000, 10000, 15000, 20000, 30000, 40000, 50000, 60000, 80000]
    types = ["exist", "false", "mine"]
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    for ttl in ttls:
        dir_name = f"sim750-{ttl}"
        if not os.path.isdir(dir_name):
            continue
        for t in types:
            sub_dir = os.path.join(dir_name, t)
            vec_path = os.path.join(sub_dir, "General-#0.vec")
            if not os.path.isfile(vec_path):
                continue
            output_file = os.path.join(results_dir, f"mars750_1_{ttl}_{t}.txt")
            
            with open(vec_path, "r", encoding="utf-8") as infile, \
                 open(output_file, "w", encoding="utf-8") as outfile:
                # Skip first 47 lines
                for _ in range(47):
                    infile.readline()
                # Process remaining lines
                for line in infile:
                    columns = line.strip().split()
                    if len(columns) < 4:
                        continue
                    # Select last two columns
                    to_write = columns[-2:]  
                    outfile.write("\t".join(to_write) + "\n")

if __name__ == "__main__":
    main()

