# Share this project with a partner

The GitHub repository contains the application source, selected five-class
labelled training dataset, a small accident-video demo, and pinned references
to the five external repositories. Download it with Git instead of compressing
the entire working folder.

## Clone everything from GitHub

```powershell
git clone --recurse-submodules https://github.com/kritarthjoshidev/Savdhan-Ai.git
cd Savdhan-Ai
```

If the repository was already cloned without submodules, run:

```powershell
git submodule update --init --recursive
```

The `external/` folder contains pinned references to A-AI, DeepCamera, Motion
Detection Alert System, my-projects, and Re-Identification-fr. They remain
their original repositories and are checked out at the versions used here.

## Recipient setup

```powershell
# Backend dependencies
cd backend
py -3.14 -m pip install -r requirements.txt

# Frontend dependencies
cd ..\frontend
npm install
```

YOLO and CLIP weights download when required. Do not commit private `.env`
files, local SQLite databases, or additional generated output.

## Included data and video

The selected five-class labelled dataset is included at:

```text
backend/auto_train_output/f898b5d3/dataset/
```

`sample_data/accident_demo.mp4` is also included as a small pipeline-test
video. The shared dataset classes are `person`, `motorcycle`, `weapon`,
`helmet`, and `car`.

The auto-training run that generated this dataset failed during training, so it
contains labelled data only, not a completed trained model. The other output
has duplicate source frames and failed-training state, so it remains local.

For offline transfer, the selected dataset can also be packed separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create_training_data_bundle.ps1
```

It creates `D:\sawdhan-ai-training-data-f898b5d3.zip`. Share larger raw videos
through Google Drive, OneDrive, or a shared folder rather than Git.

## Create a compact source bundle (optional)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create_source_bundle.ps1
```

It creates `D:\sawdhan-ai-source.zip` and excludes downloaded weights,
dependencies, local configuration, and generated files.
