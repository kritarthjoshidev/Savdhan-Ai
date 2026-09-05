# Savdhan AI — Border Surveillance Command Center

Savdhan AI is a FastAPI and React project for real-time border-surveillance
analytics. Its backend combines motion gating, CLAHE low-light enhancement,
YOLO-World detection, virtual-fence intrusion detection, person re-ID, incident
records, and WebSocket alerts.

## Clone the complete project

```powershell
git clone --recurse-submodules https://github.com/kritarthjoshidev/Savdhan-Ai.git
cd Savdhan-Ai
```

The five external reference projects are included as pinned Git submodules.
For an existing clone, fetch them with:

```powershell
git submodule update --init --recursive
```

## Included assets

- Application source for `backend/` and `frontend/`
- Five-class labelled training dataset at
  `backend/auto_train_output/f898b5d3/dataset/`
- `sample_data/accident_demo.mp4` for local pipeline testing
- Pinned external repositories under `external/`

Downloaded model weights, Python/Node virtual environments, local databases,
logs, and failed/duplicate training outputs are intentionally excluded. The
CLIP weights are about 338 MB each and exceed GitHub's normal 100 MB file limit;
the application downloads required YOLO and CLIP models when needed.

## Setup

```powershell
# Backend
cd backend
py -3.14 -m pip install -r requirements.txt

# Frontend (from project root)
cd ..\frontend
npm install
```

See [backend/START_HERE.md](backend/START_HERE.md) for backend setup and
[SHARE_WITH_PARTNER.md](SHARE_WITH_PARTNER.md) for the full sharing notes.

## Review evidence and live phone cameras

Every named incident (`BORDER_INTRUSION` or `TRAFFIC_ACCIDENT`) captures an
annotated detection image, nearby frames, and a short context clip. Review
these directly in **Incidents** before verifying or rejecting an alert; no
manual local-file navigation is required.

To use an Android phone as a CCTV source, follow
[backend/PHONE_CAMERA_SETUP.md](backend/PHONE_CAMERA_SETUP.md). The **Live
Camera Command** page tests, saves, previews, and starts the protected camera.
Choose its Border, Traffic, or Auto profile before pressing **Protect**.
