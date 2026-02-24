import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Union
from pathlib import Path
from enum_utils import FormattedIntEnum

import pykinect_azure as pykinect

logger = logging.getLogger(__name__)

class KinectJoint(FormattedIntEnum):
    PELVIS = 0
    SPINE_NAVEL = 1
    SPINE_CHEST = 2
    NECK = 3
    CLAVICLE_LEFT = 4
    SHOULDER_LEFT = 5
    ELBOW_LEFT = 6
    WRIST_LEFT = 7
    HAND_LEFT = 8
    HANDTIP_LEFT = 9
    THUMB_LEFT = 10
    CLAVICLE_RIGHT = 11
    SHOULDER_RIGHT = 12
    ELBOW_RIGHT = 13
    WRIST_RIGHT = 14
    HAND_RIGHT = 15
    HANDTIP_RIGHT = 16
    THUMB_RIGHT = 17
    HIP_LEFT = 18
    KNEE_LEFT = 19
    ANKLE_LEFT = 20
    FOOT_LEFT = 21
    HIP_RIGHT = 22
    KNEE_RIGHT = 23
    ANKLE_RIGHT = 24
    FOOT_RIGHT = 25
    HEAD = 26
    NOSE = 27
    EYE_LEFT = 28
    EAR_LEFT = 29
    EYE_RIGHT = 30
    EAR_RIGHT = 31

class KinectConfidence(FormattedIntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

class DatasetBuilderBase(ABC):
    """Abstract base class for dataset builders."""
    
    # Class-level flag to ensure global initialization runs only once
    _is_initialized: bool = False
    
    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir
        if not self.__class__._is_initialized:
            self._global_initialize()
            self.__class__._is_initialized = True

    def _global_initialize(self) -> None:
        """Initialize globally once for all dataset builders."""
        logger.debug("Start global initialization...")
        
        # NOTE: The substring 'k4a' must not be included anywhere in the folder path.
        # This is because pykinect internally searches for the k4arecord.dll path
        # by simply replacing the string 'k4a' with 'k4arecord' in the path string.
        # TODO: Handle this issue.
        kinect_sdk_dir = Path(__file__).parent / '../.kinect-sdk'
        k4a_dll_path = str(kinect_sdk_dir / 'k4a.dll') if kinect_sdk_dir.exists() else None
        k4abt_dll_path = str(kinect_sdk_dir / 'k4abt.dll') if kinect_sdk_dir.exists() else None
        
        pykinect.initialize_libraries(
            module_k4a_path=k4a_dll_path,
            module_k4abt_path=k4abt_dll_path,
            track_body=True
        )

        logger.debug("Global initialization completed.")
    
    def process(self, input_path: Union[Path, str]) -> None:
        """Process the input file and generate the dataset."""
        input_path = Path(input_path).resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_dir_path = (self.output_dir or input_path.parent / input_path.stem).resolve()
        
        logger.info(f"--- Processing started for: {input_path.name} ---")
        logger.info(f"Target file: {input_path}")
        logger.info(f"Output directory: {output_dir_path}")
        
        self._setup_directories(output_dir_path)
        self._process_impl(input_path, output_dir_path)
        logger.info("--- Processing completed successfully ---")

    def _setup_directories(self, output_dir_path: Path) -> None:
        """Create necessary output directory structure."""
        for dir_name in self.required_directories:
            dir_path = output_dir_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

    @property
    @abstractmethod
    def required_directories(self) -> List[str]:
        """Define a list of directory names that need to be created."""
        pass

    @abstractmethod
    def _process_impl(self, input_path: Path, output_dir_path: Path) -> None:
        """Implementation of the dataset extraction process."""
        pass
