import json
import logging
from typing import Optional, Tuple, Any, List
from pathlib import Path

import cv2
import numpy as np
import pykinect_azure as pykinect

from builder_base import DatasetBuilderBase, KinectJoint, KinectConfidence

logger = logging.getLogger(__name__)

class RGBDatasetBuilder(DatasetBuilderBase):
    """Dataset builder for extracting 2D RGB frames and 3D skeletons from Azure Kinect MKV recordings."""

    @property
    def required_directories(self) -> List[str]:
        return ['rgb-frames', 'body-frames', 'annotated-rgb-frames']

    def _process_impl(self, 
        input_path: Path, 
        output_dir_path: Path
    ) -> None:
        playback = pykinect.start_playback(str(input_path))
        calibration = playback.get_calibration()
        tracker = pykinect.start_body_tracker(calibration=calibration)

        def _object_to_dict(obj):
            res = {}
            for attr in dir(obj):
                if attr.startswith('_'): continue
                val = getattr(obj, attr)
                if not callable(val): res[attr] = val
            return res

        record_conf = playback.get_record_configuration()
        calib_dict = {
            "color_params": _object_to_dict(calibration.color_params),
            "depth_params": _object_to_dict(calibration.depth_params),
            'record_conf': {
                'color_format': ['JPG', 'NV12', 'YUY2', 'BGRA32'][record_conf.handle().color_format], # 0:JPG, 1:NV12, 2:YUY2, 3:BGRA32
                'color_resolution': ['OFF', '720p', '1080p', '1440p', '1536p', '2160p', '3072p'][record_conf.handle().color_resolution], # 0:OFF, 1:720p, 2:1080p, 3:1440p, 4:1536p, 5:2160p, 6:3072p
                'depth_mode': ['OFF', 'NFOV_2X2BINNED', 'NFOV_UNBINNED', 'WFOV_2X2BINNED', 'WFOV_UNBINNED', 'Passive IR'][record_conf.handle().depth_mode], # 0:OFF, 1:NFOV_2X2BINNED, 2:NFOV_UNBINNED,3:WFOV_2X2BINNED, 4:WFOV_UNBINNED, 5:Passive IR
                'camera_fps': [5, 15, 30][record_conf.handle().camera_fps], # 0:5 FPS, 1:15 FPS, 2:30 FPS
                #'color_track_enabled': record_conf.handle().color_track_enabled, # True of False. If Color camera images exist
                #'depth_track_enabled': record_conf.handle().depth_track_enabled, # True of False. If Depth camera images exist
                #'ir_track_enabled': record_conf.handle().ir_track_enabled, # True of False. If IR camera images exist
                #'imu_track_enabled': record_conf.handle().imu_track_enabled, # True of False. If IMU samples exist
                #'depth_delay_off_color_usec': record_conf.handle().depth_delay_off_color_usec, # Delay between the color image and the depth image
                #'wired_sync_mode': ['Standalone', 'Master', 'Subordinate'][record_conf.handle().wired_sync_mode], # 0:Standalone mode, 1:Master mode, 2:Subordinate mode
                #'subordinate_delay_off_master_usec': record_conf.handle().subordinate_delay_off_master_usec, # The external synchronization timing.
                #'start_timestamp_offset_usec': record_conf.handle().start_timestamp_offset_usec, # Start timestamp offset.
            }
        }

        json_path = output_dir_path / 'calib_info.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(calib_dict, f, indent=2)

        frame_idx = 0
        try:
            while True:
                success, capture = playback.update()
                if not success:
                    break
                
                self._process_frame(
                    capture=capture, 
                    tracker=tracker, 
                    frame_idx=frame_idx, 
                    output_dir_path=output_dir_path
                )
                frame_idx += 1
                
        except KeyboardInterrupt:
            logger.info("User interrupt.")
        finally:
            cv2.destroyAllWindows()
            logger.info(f"Total {frame_idx} frames processed.")

    def _process_frame(self, 
        capture: pykinect.Capture, 
        tracker: pykinect.Tracker, 
        frame_idx: int, 
        output_dir_path: Path
    ) -> None:
        ret, color_image = capture.get_color_image()
        body_frame = tracker.update(capture)

        timestamp_us = self._get_timestamp(
            capture=capture, 
            body_frame=body_frame, 
            frame_idx=frame_idx
        )

        primary_body, primary_body_idx = self._find_primary_body(
            body_frame=body_frame
        )
        
        # Save body parsing data
        if primary_body:
            self._save_body_data(
                body=primary_body, 
                body_id=body_frame.get_body_id(index=primary_body_idx),
                timestamp_us=timestamp_us, 
                frame_idx=frame_idx, 
                output_dir_path=output_dir_path
            )

        # Save RGB and Annotated frames
        if ret and color_image is not None:
            self._save_rgb_frame(
                color_image=color_image, 
                frame_idx=frame_idx, 
                output_dir_path=output_dir_path
            )
            self._save_annotated_rgb_frame(
                color_image=color_image, 
                timestamp_us=timestamp_us, 
                body_frame=body_frame, 
                body_idx=primary_body_idx, 
                frame_idx=frame_idx, 
                output_dir_path=output_dir_path
            )

    @staticmethod
    def _get_timestamp(
        capture: pykinect.Capture, 
        body_frame: pykinect.k4abt.Frame, frame_idx: int
    ) -> int:
        if body_frame and hasattr(body_frame, 'get_device_timestamp_usec'):
            return body_frame.get_device_timestamp_usec()
        if hasattr(capture, 'get_device_timestamp_usec'):
            return capture.get_device_timestamp_usec()
        return frame_idx * 33333

    @staticmethod
    def _find_primary_body(
        body_frame: pykinect.k4abt.Frame
    ) -> Tuple[Optional[pykinect.k4abt.Frame], Optional[int]]:
        if not body_frame or not body_frame.is_valid():
            return None, None

        num_bodies = body_frame.get_num_bodies()
        if num_bodies == 0:
            return None, None

        min_dist_x = float('inf')
        primary_body = None
        primary_body_idx = None

        for i in range(num_bodies):
            body = body_frame.get_body(i)
            pelvis = body.joints[pykinect.K4ABT_JOINT_PELVIS]
            
            # Find the person closest to the vertical axis of the camera's field of view.
            dist_x = abs(pelvis.position.x)
            if dist_x < min_dist_x:
                min_dist_x = dist_x
                primary_body = body
                primary_body_idx = i

        return primary_body, primary_body_idx

    @staticmethod
    def _save_body_data(
        body: pykinect.Body, 
        body_id: int,
        timestamp_us: int, 
        frame_idx: int, 
        output_dir_path: Path
    ) -> None:
        skeleton_dict = {}
        for j_enum in KinectJoint:
            j_idx = j_enum.value
            if j_idx < len(body.joints):
                jdata = body.joints[j_idx]
                skeleton_dict[j_enum.formatted_name] = {
                    'position': {
                        'x': jdata.position.x,
                        'y': jdata.position.y,
                        'z': jdata.position.z
                    },
                    'confidence': KinectConfidence(jdata.confidence_level).formatted_name
                }
        
        body_dict = {
            'body-id': body_id,
            'timestamp-us': timestamp_us,
            'skeleton': skeleton_dict
        }

        json_path = output_dir_path / 'body-frames' / f'{frame_idx:04d}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(body_dict, f)

    @staticmethod
    def _save_rgb_frame(
        color_image: np.ndarray, 
        frame_idx: int, 
        output_dir_path: Path
    ) -> None:
        rgb_path = output_dir_path / 'rgb-frames' / f'{frame_idx:04d}.png'
        cv2.imwrite(str(rgb_path), color_image)

    @staticmethod
    def _save_annotated_rgb_frame(
        color_image: np.ndarray, 
        timestamp_us: int, 
        body_frame: Any, 
        body_idx: Optional[int],
        frame_idx: int,
        output_dir_path: Path
    ) -> None:
        annotate_img = color_image.copy()

        if body_frame and body_frame.is_valid() and body_idx is not None:
            annotate_img = body_frame.draw_body2d(
                annotate_img, 
                bodyIdx=body_idx, 
                dest_camera=pykinect.K4A_CALIBRATION_TYPE_COLOR
            )
        
        cv2.putText(
            annotate_img,
            f'Timestamp: {timestamp_us} us',
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        annotated_path = output_dir_path / 'annotated-rgb-frames' / f'{frame_idx:04d}.jpg'
        cv2.imwrite(str(annotated_path), annotate_img, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        
        cv2.imshow('Annotated Frame', annotate_img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            raise KeyboardInterrupt
