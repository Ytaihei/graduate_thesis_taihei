#!/usr/bin/env python3
import os

def main():
    ttls = [10,50,100,150,200,250,300,350,400,450,500,1000]
    types = ["exist", "false", "mine"]
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    for ttl in ttls:
        dir_name = f"simmoon-{ttl}"
        if not os.path.isdir(dir_name):
            continue
        for t in types:
            sub_dir = os.path.join(dir_name, t)
            vec_path = os.path.join(sub_dir, "General-#0.vec")
            if not os.path.isfile(vec_path):
                continue
            output_file = os.path.join(results_dir, f"moon_1_{ttl}_{t}.txt")
            
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

