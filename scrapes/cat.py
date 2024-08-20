import os
import json


def concatenate_jsonl_files(input_dir):
    output_filename = os.path.join(input_dir, "all_candidate_tasks.jsonl")
    tasks_dir = os.path.join(input_dir, "tasks")
    jsonl_files = [f for f in os.listdir(tasks_dir) if f.endswith(".jsonl")]
    print(jsonl_files)
    assert len(jsonl_files) > 0, "No JSONL files found in the tasks directory."
    total_lines = 0
    with open(output_filename, "w") as outfile:
        for fname in jsonl_files:
            with open(os.path.join(tasks_dir, fname)) as infile:
                for line in infile:
                    outfile.write(line)
                    total_lines += 1

    with open(output_filename) as outfile:
        output_lines = sum(1 for _ in outfile)

    assert (
        output_lines == total_lines
    ), "The number of lines in the output file does not match the total number of lines in the input files."


if __name__ == "__main__":
    input_directory = input("Enter the input directory path: ")
    concatenate_jsonl_files(input_directory)
