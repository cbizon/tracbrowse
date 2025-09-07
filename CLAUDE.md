# Simple Predictions

## Goal

We are working on biomedical knowledge graphs.  We are trying to find the graph edges that influence a new edge prediction.

## Basic Setup

* github: The project is not in github yet, but we will want it.
* conda: we are using conda for package management with an env called "trac"
* tests: we are using pytest, and want to maintain high code coverage

## Input

The input data may never be changed.  

It consists of files like this:

TestHead,TestHead_label,TestRel,TestRel_label,TestTail,TestTail_label,TrainHead,TrainHead_label,TrainRel,TrainRel_label,TrainTail,TrainTail_label,TracInScore
UNII:U59UGK3IPC,Ublituximab,predicate:27,biolink:treats,MONDO:0005314,relapsing-remitting multiple sclerosis,NCBIGene:3455,IFNAR2,predicate:29,biolink:target_for,MONDO:0005314,relapsing-remitting multiple sclerosis,0.3972736001014709
UNII:U59UGK3IPC,Ublituximab,predicate:27,biolink:treats,MONDO:0005314,relapsing-remitting multiple sclerosis,NCBIGene:3455,IFNAR2,predicate:29,biolink:target_for,MONDO:0005314,relapsing-remitting multiple sclerosis,0.3972736001014709
UNII:U59UGK3IPC,Ublituximab,predicate:27,biolink:treats,MONDO:0005314,relapsing-remitting multiple sclerosis,NCBIGene:8698,S1PR4,predicate:29,biolink:target_for,MONDO:0005314,relapsing-remitting multiple sclerosis,0.3969393968582153
UNII:U59UGK3IPC,Ublituximab,predicate:27,biolink:treats,MONDO:0005314,relapsing-remitting multiple sclerosis,NCBIGene:55244,SLC47A1,predicate:29,biolink:target_for,MONDO:0005314,relapsing-remitting multiple sclerosis,0.3893853425979614
UNII:U59UGK3IPC,Ublituximab,predicate:27,biolink:treats,MONDO:0005314,relapsing-remitting multiple sclerosis,NCBIGene:146802,SLC47A2,predicate:29,biolink:target_for,MONDO:0005314,relapsing-remitting multiple sclerosis,0.3874559998512268

TestHead and TestTail (and their labels) are the predicted edge.

The TrainHead and TrainTail (and their labels) are the edges we want to understand and display.   The last column, TracInScore, tells us how important each input edge is to the predicted edge.

## Filtered input

/src/top_scores.py filters these big files to just the highest scoring edges.

### Usage Examples:
```bash
# Get top 100,000 scores from default input file
python src/top_scores.py 100000

# Process a specific file
python src/top_scores.py input_data/myfile.csv 50000

# Specify custom output location
python src/top_scores.py 100000 -o filtered_data/custom_output.csv
```

## Project structure
```
/input_data/              # Raw input files (never modified)
  └── influencescores_testtreatsedge1.csv
/filtered_data/           # Processed top-N scoring edges
  └── treats1_top_100000_results.csv
/src/
  ├── top_scores.py       # Filters input data to top-N scores
  └── webapp.py           # Flask visualization app
```

## Webapp

`/src/webapp.py` is a Flask app that visualizes the graph edges. Features:
- **Interactive D3.js graph** with force-directed layout
- **Configurable edge count** (1-10,000 edges)
- **De-hairing toggle** to remove degree-1 nodes iteratively
- **Color-coded entities**: Red for test prediction entities, teal for training-only
- **Hover tooltips** with entity and edge details
- **Statistics panel** showing node/edge counts and de-hairing results

### Running the webapp:
```bash
# Activate conda environment
conda activate trac

# Start the webapp on port 5090
python src/webapp.py
```

Then visit: http://localhost:5090
