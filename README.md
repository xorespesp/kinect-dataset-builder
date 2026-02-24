# kinect-dataset-builder

Extracts RGB videos and tracks 3D skeleton data using the Azure Kinect Sensor SDK.

## Quickstart
Clone the repository and navigate to the project root:
```bash
$ git clone https://github.com/xorespesp/kinect-dataset-builder.git
$ cd kinect-dataset-builder
```

Install [uv](https://docs.astral.sh/uv/) and the required dependencies:
```bash
$ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$ powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_kinect_sdk.ps1
$ uv sync
```

Once installed, run the following command to generate the dataset from an MKV file:
```bash
$ uv run src\main.py <path_to_input.mkv>
```

---

## Output Dataset Format

Outputs will be saved in a new dataset directory named after the MKV file.  
The directory structure is as follows:

```text
/<dataset_root>
 +-- /rgb-frames
 |    +-- 0000.png
 |    +-- 0001.png
 |    +-- ...
 +-- /annotated-rgb-frames
 |    +-- 0000.jpg
 |    +-- 0001.jpg
 |    +-- ...
 +-- /body-frames
      +-- 0000.json
      +-- 0001.json
      +-- ...
```

- `rgb-frames/`: Contains extracted RGB color images for each frame.
- `annotated-rgb-frames/`: Contains RGB frames overlaid with 3D tracked skeleton visualizations.
- `body-frames/`: Contains tracked 3D skeleton data for each frame. The format of each JSON file is as follows:

```json
{
    "body-id": 1,
    "timestamp-us": 1234567,
    "skeleton": {
        "pelvis": {
            "position": { "x": 1.0, "y": 2.0, "z": 3.0 },
            "confidence": "high"
        },
        "spine_navel": {
            "position": { "x": 4.0, "y": 5.0, "z": 6.0 },
            "confidence": "medium"
        }
        // ...
    }
}
```

### Tracked Joints Hierarchy (Total 32 Joints)

| Joint Name | Parent Joint |
|---|---|
| `pelvis` | *None (Root)* |
| `spine_navel` | `pelvis` |
| `spine_chest` | `spine_navel` |
| `neck` | `spine_chest` |
| `clavicle_left` | `spine_chest` |
| `shoulder_left` | `clavicle_left` |
| `elbow_left` | `shoulder_left` |
| `wrist_left` | `elbow_left` |
| `hand_left` | `wrist_left` |
| `handtip_left` | `hand_left` |
| `thumb_left` | `wrist_left` |
| `clavicle_right` | `spine_chest` |
| `shoulder_right` | `clavicle_right` |
| `elbow_right` | `shoulder_right` |
| `wrist_right` | `elbow_right` |
| `hand_right` | `wrist_right` |
| `handtip_right` | `hand_right` |
| `thumb_right` | `wrist_right` |
| `hip_left` | `pelvis` |
| `knee_left` | `hip_left` |
| `ankle_left` | `knee_left` |
| `foot_left` | `ankle_left` |
| `hip_right` | `pelvis` |
| `knee_right` | `hip_right` |
| `ankle_right` | `knee_right` |
| `foot_right` | `ankle_right` |
| `head` | `neck` |
| `nose` | `head` |
| `eye_left` | `head` |
| `ear_left` | `head` |
| `eye_right` | `head` |
| `ear_right` | `head` |

### Confidence Levels
| Level | Description |
|---|---|
| `none` | The joint is out of range or not tracked |
| `low` | The joint is not observed (likely occluded) and is predicted |
| `medium` | Medium confidence in joint pose |
| `high` | High confidence in joint pose |
