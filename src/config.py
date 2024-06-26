import locale
import sys
from enum import Enum, auto
from pathlib import Path

import loguru
from qfluentwidgets import (BoolValidator, ConfigItem, ConfigValidator, EnumSerializer, FolderValidator,
                            OptionsConfigItem, OptionsValidator, QConfig, RangeConfigItem, RangeValidator, qconfig)

from src.core.paths import (CONFIG_FILE, FFMPEG_FILE, NOISE_REDUCE_MODEL_FILE, OUTPUT_FILE, ROOT, TEMP_DIR)

if sys.getdefaultencoding() != 'utf-8':
    import importlib

    importlib.reload(sys)
    loguru.logger.debug(f"系统默认编码: {sys.getdefaultencoding()}, 已经重新加载为UTF-8")

# # 确保环境变量LANG设置为UTF-8
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


# 去黑边算法
class BlackBorderAlgorithm(Enum):
    DISABLE = 0
    STATIC = auto()
    DYNAMIC = auto()


# 音频响度标准化标准
class AudioNormalization(Enum):
    DISABLE = ""
    RADIO = "loudnorm=i=-15.0:lra=2.0:tp=-1.0:"
    TV = "loudnorm=i=-24.0:lra=2.0:tp=-1.0:"
    MOVIE = "loudnorm=i=-24.0:lra=7.0:tp=-2.0:"


# 音频降噪策略
class AudioNoiseReduction(Enum):
    DISABLE = ""
    STATIC = "highpass=200,lowpass=3000,afftdn"  # 一个很好地组合过滤器
    AI = f'arnndn=model={NOISE_REDUCE_MODEL_FILE.relative_to(ROOT)}'  # AI降噪


# 视频降噪策略
class VideoNoiseReduction(Enum):
    DISABLE = ""
    HQDN3D = "hqdn3d=4.0:3.0:6.0:4.5"  # 快速降噪滤镜
    NLMEANS = "nlmeans=6.0:7.0"  # 非局部均值降噪滤镜, 更慢, 但效果更好


# 补帧策略
class FrameRateAdjustment(Enum):
    NORMAL = 1
    MOTION_INTERPOLATION = 2


# 缩放质量
class ScalingQuality(Enum):
    NEAREST = 'neighbor'
    BILINEAR = 'bilinear'
    BICUBIC = 'bicubic'
    LANCZOS = 'lanczos'
    SINC = "sinc"


# 视频编码策略
class VideoCodec(Enum):
    H264 = "-c:v libx264 -crf 23 -preset slow -qcomp 0.5 -psy-rd 0.3:0 -aq-mode 2 -aq-strength 0.8"
    H264Intel = "-c:v h264_qsv -qscale 15"
    H264AMD = "-c:v h264_amf -qscale 15"
    H264Nvidia = "-c:v h264_nvenc -qscale 15"
    H265 = "-c:v libx265 -crf 28"
    H265Intel = "-c:v hevc_qsv -qscale 15"
    H265AMD = "-c:v hevc_amf -qscale 15"
    H265Nvidia = "-c:v hevc_nvenc -qscale 15"


# 预览视频帧
class PreviewFrame(Enum):
    FirstFrame = 1
    LastFrame = 2
    RandomFrame = 3


# 音频采样率
class AudioSampleRate(Enum):
    Hz8000 = 8000
    Hz16000 = 16000
    Hz22050 = 22050
    Hz32000 = 32000
    Hz44100 = 44100
    Hz96000 = 96000
    Max = 0


class OutputFileValidator(ConfigValidator):
    """ Config validator """

    def validate(self, value):
        """ Verify whether the value is legal """
        file_path: Path = Path(value)
        return bool(file_path.is_file())

    def correct(self, value):
        """ correct illegal value """
        file_path: Path = Path(value)
        return value if file_path.is_file() else str(OUTPUT_FILE)


class FFmpegValidator(ConfigValidator):
    """ Config validator """

    def validate(self, value):
        """ Verify whether the value is legal """
        ffmpeg_path: Path = Path(value)
        return bool(ffmpeg_path.is_file() and ffmpeg_path.suffix == '.exe')

    def correct(self, value):
        """ correct illegal value """
        ffmpeg_path: Path = Path(value)
        if ffmpeg_path.is_file() and ffmpeg_path.suffix == '.exe':
            return value
        return str(FFMPEG_FILE)


class Config(QConfig):
    # 视频质量
    output_file_path = ConfigItem("Video", "输出文件路径", str(OUTPUT_FILE), OutputFileValidator())
    shake = ConfigItem("Video", "视频去抖动", False, BoolValidator())
    deband = ConfigItem("Video", "视频去色带", False, BoolValidator())
    deblock = ConfigItem("Video", "视频去色块", False, BoolValidator())
    video_fps = RangeConfigItem("Video", "目标视频帧率", 30, RangeValidator(1, 144))
    video_sample_frame_number = RangeConfigItem("Video", "去黑边采样帧数", 500, RangeValidator(100, 2000))
    video_black_border_algorithm = OptionsConfigItem("Video", "黑边去除算法", BlackBorderAlgorithm.DYNAMIC,
                                                     OptionsValidator(BlackBorderAlgorithm),
                                                     EnumSerializer(BlackBorderAlgorithm))
    audio_normalization = OptionsConfigItem("Video", "音频响度标准化", AudioNormalization.DISABLE,
                                            OptionsValidator(AudioNormalization), EnumSerializer(AudioNormalization))
    audio_noise_reduction = OptionsConfigItem("Video", "音频降噪", AudioNoiseReduction.AI,
                                              OptionsValidator(AudioNoiseReduction),
                                              EnumSerializer(AudioNoiseReduction))
    video_noise_reduction = OptionsConfigItem("Video", "视频降噪", VideoNoiseReduction.HQDN3D,
                                              OptionsValidator(VideoNoiseReduction),
                                              EnumSerializer(VideoNoiseReduction))
    scaling_quality = OptionsConfigItem("Video", "缩放质量", ScalingQuality.SINC, OptionsValidator(ScalingQuality),
                                        EnumSerializer(ScalingQuality))
    rate_adjustment_type = OptionsConfigItem("Video", "补帧策略", FrameRateAdjustment.NORMAL,
                                             OptionsValidator(FrameRateAdjustment), EnumSerializer(FrameRateAdjustment))
    output_codec = OptionsConfigItem("Video", "输出编码策略", VideoCodec.H264, OptionsValidator(VideoCodec),
                                     EnumSerializer(VideoCodec))
    audio_sample_rate = OptionsConfigItem("Video", "音频采样率", AudioSampleRate.Hz44100,
                                          OptionsValidator(AudioSampleRate), EnumSerializer(AudioSampleRate))

    # 全局设置
    ffmpeg_file = ConfigItem("General", "FFmpeg路径", str(FFMPEG_FILE), FFmpegValidator())
    temp_dir = ConfigItem("General", "临时目录", str(TEMP_DIR), FolderValidator())
    delete_temp_dir = ConfigItem("General", "完成后删除临时目录", True, BoolValidator())
    preview_video_remove_black = ConfigItem("General", "预览视频是否去黑边", False, BoolValidator())
    preview_frame = OptionsConfigItem("General", "预览视频帧", PreviewFrame.FirstFrame, OptionsValidator(PreviewFrame),
                                      EnumSerializer(PreviewFrame))
    preview_auto_play = ConfigItem("General", "预览视频自动播放", False, BoolValidator())


cfg = Config()
cfg.file = CONFIG_FILE
if not CONFIG_FILE.exists():
    cfg.save()
qconfig.load(CONFIG_FILE, cfg)
