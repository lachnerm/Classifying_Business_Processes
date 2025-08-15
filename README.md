# Classifying Business Processes by Level of Structuredness: A Relationship-Based Approach

This repository contains the source code for running and evaluating a structuredness classification algorithm on business process event logs.  

## Abstract

The choice of a suitable modeling notation in process discovery depends on the **structuredness** of the process. Structured processes are best captured in imperative notations, loosely structured and knowledge-intensive processes benefit from declarative notations, and semi-structured processes often require hybrid approaches. However, current process mining practice provides little systematic guidance for assessing structuredness before discovery.

This repository implements an **automated classification algorithm** that determines the structuredness of a business process from activity relationship data. The method analyzes temporal and existential dependencies between activities to detect characteristic workflow patterns and compute aggregated relationship metrics. These components are combined into a continuous structuredness score, which is compared against thresholds to assign the process to one of four classes: `structured`, `semiStructured`, `looselyStructured`, or `unstructured`.

The tool enables process analysts to pre-classify processes before modeling, supporting the selection of an appropriate notation and improving the practical value of discovered models.


## Overview

The **Process Structuredness Classifier** is a Python-based command-line tool that:

- Loads temporal and existential activity relationships from preprocessed data files.
- Detects control-flow blocks (e.g., XOR, PAR) and aggregates related blocks into larger structured process fragments ("super-blocks").
- Scores the process based on a set of reference metrics.
- Maps the score to a structuredness class using configurable thresholds.

## Features

- Four-class classification: `unstructured`, `looselyStructured`, `semiStructured`, `structured`
- Modular architecture: block detection, block aggregation, scoring.
- Verbose mode for detailed inspection of detected structures.
- Configurable metrics and thresholds (`constants.py`).
- Tabular summary output for multiple process logs.

## Requirements

- Python 3.8 or higher
- Required Python packages (see `requirements.txt`):

## Installation

1. Clone the repository:
    ```sh
    git clone git@github.com:INSM-TUM/process-classification-activity-relationships.git
    cd process-classification-activity-relationships
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Command-Line Interface

Run the classification:

`python classify_process.py --dir <path_to_data> [--verbose]`

#### Arguments

- `--dir` (string, optional): Directory containing the input files (default: `data_evaluation/data`).
- `--verbose` (flag, optional): Enables detailed output of detected blocks, super-blocks, and scoring.

### Example

`python classify.py --dir data_evaluation/data --verbose`

### Input Files

The classifier expects input files in **JSON format** containing precomputed **pairwise activity relationships** (temporal + existential) for a process.  
Files must follow the naming pattern:

`<log_name>_<true_class>.json`  
Example:  
`Order_Processing_structured.json`

#### How to generate the JSON input files

1. **Start from an Event Log in XES format**  
   You need an event log that represents the process you want to classify. This should be in the standard `.xes` format.

2. **Generate the Activity Relationship Matrix (YAML)**  
   Use the [activity-relationship-matrix-discovery](https://github.com/INSM-TUM/activity-relationship-matrix-discovery) tool to transform the event log into a YAML file containing the activity relationship matrix.  
   This tool computes **temporal** and **existential** dependencies between each pair of activities.  
   Export the result as a `.yaml` file.

3. **Convert the YAML to JSON**  
   In this repository, there is a helper script at:  
   `helper/matrix_yaml_to_json.py`  
   Running this script will read the `.yaml` file from step 2 and convert it into the correct JSON format required by the classifier.

4. **Place the JSON file in your chosen input directory**  
   Name it according to the expected pattern (`<log_name>_<true_class>.json`) and store it in the folder you will pass to the `--dir` argument when running the classifier.

### Output

- **Console table** summarizing results across all input files, for example:

  | Log              | #SBs | Insiders | Outsiders | Base-Score | SB vs. SB | Out vs. SB | Out vs. Out | Refinement | Score | Class Real  | Class Calculated | Match |
  |------------------|------|----------|-----------|------------|-----------|------------|-------------|------------|-------|-------------|------------------|-------|
  | Order_Processing |  2   | A,B,C,D  | E,F       | 0.66       | 0.15      | 0.10       | 0.10        | 0.25       | 0.81  | structured  | structured       | ✅    |

- In verbose mode, detected **blocks** and **super-blocks** as well as details about all refinements and metrics are printed for each file.

## Project Structure

### Code Files

- `classify_process.py`: Main script to run the classification. Handles command-line arguments, calls the classification pipeline, and prints the results table.
- `block_detection.py`: Implements the detection of control-flow blocks (e.g., XOR, PAR) and the combination of these into super-blocks.
- `score_process.py`: Computes process metrics based on detected structures and calculates the final structuredness score.
- `utils.py`: Contains data loading functions and helper utilities for working with activity relationships.
- `constants.py`: Defines configurable thresholds and other constants used throughout the project.
- `helper/matrix_yaml_to_json.py`: Utility script to convert YAML-formatted activity relationship matrices into the JSON format required by the classifier.
- `helper/count_trace_variants.py`: Script to load an event log in XES format, identify unique trace variants, and print their counts.
- `helper/verify_block_detection.py`: Test utility that compares detected control-flow blocks and super-blocks for the development data against expected outputs, useful for verifying correctness after logic changes.

### Example Data

- `data_development/`: Dataset used during the algorithm’s iterative development phase. Contains:
  - JSON files in the correct input format for the classifier.
  - Event logs in `.xes` format.
  - BPMN process models (where applicable).
  - Images of the process models for reference.

- `data_evaluation/`: Independent dataset used for evaluation and testing of the final algorithm. Contains:
  - JSON files in the correct input format for the classifier.
  - Event logs in `.xes` format.
  - BPMN process models (where applicable).
  - Images of the process models for reference.


## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or issues, please contact:

- **Kerstin Andree** ([kerstin.andree@tum.de](mailto:kerstin.andree@tum.de))
- **Michael Lachner** ([m.lachner@tum.de](mailto:m.lachner@tum.de))


