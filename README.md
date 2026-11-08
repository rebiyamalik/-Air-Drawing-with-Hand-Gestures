# Air Drawing with Hand Gestures 🖐️

Draw in the air using your webcam, Python, OpenCV, and MediaPipe.

## Features
- Real-time hand landmark tracking
- Index finger: draw
- Index + middle fingers: move without drawing
- Closed four fingers: erase
- Four fingers raised: clear canvas
- Keyboard shortcuts for colors and brush size
- Save drawings as PNG files

## Requirements
- Python 3.10 or 3.11 recommended
- Webcam
- Windows, macOS, or Linux

## Install (Windows)

```powershell
git clone https://github.com/rebiyamalik/-Air-Drawing-with-Hand-Gestures.git
cd -Air-Drawing-with-Hand-Gestures
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py
```

## Gestures

| Gesture | Action |
| --- | --- |
| Index finger raised | Draw |
| Index + middle fingers raised | Move pointer |
| Four fingers folded | Erase |
| Four fingers raised | Clear canvas |

The detector uses index, middle, ring, and pinky fingers and ignores the thumb because thumb orientation changes with hand rotation.

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| 1-5 | Choose blue, green, red, yellow, or white |
| + / - | Increase / decrease brush size |
| C | Clear canvas |
| S | Save PNG in `output/` |
| Q / Esc | Quit |

## Troubleshooting
- If the webcam does not open, close other camera apps, check Windows camera permissions, or try changing camera index from 0 to 1.
- If MediaPipe installation fails, use Python 3.10 or 3.11 in a fresh virtual environment.
- Run locally on a desktop because OpenCV GUI windows may not work in headless terminals.

## Project status
Initial prototype. Gesture detection may need tuning for different lighting, camera angles, and hand positions.

## License
MIT
