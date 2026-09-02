# Share this project without the large local files

Do not compress the entire working folder. It contains downloaded models,
external reference repositories, Python/Node dependencies, generated training
data, local databases, and machine-specific configuration.

## Create the compact source bundle

From the project root in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create_source_bundle.ps1
```

It creates `D:\sawdhan-ai-source.zip` and excludes local-only/generated files.
Your original project files are not deleted or moved.

## Recipient setup

After extracting the archive, the partner can run:

```powershell
# Optional: obtain the five reference repositories again
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\clone_external_repos.ps1

# Backend dependencies
cd backend
py -3.14 -m pip install -r requirements.txt

# Frontend dependencies
cd ..\frontend
npm install
```

YOLO and CLIP weights download when required. Do not include private `.env`
files, local SQLite databases, or training/video data in the source bundle.

## Sharing training data and videos

The current project has two auto-train outputs with duplicate source frames.
Share only the five-class dataset from job `f898b5d3` separately:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create_training_data_bundle.ps1
```

It creates `D:\sawdhan-ai-training-data-f898b5d3.zip`. Send that archive and
raw videos through Google Drive, OneDrive, or a shared folder; do not put raw
footage or generated output inside Git.

The recipient should extract the data archive so this path exists:

```text
backend/auto_train_output/f898b5d3/dataset/
```

The shared dataset classes are `person`, `motorcycle`, `weapon`, `helmet`, and
`car`. The auto-training runs that generated these datasets failed during
training, so this archive contains labelled data only—not a completed trained
model.
