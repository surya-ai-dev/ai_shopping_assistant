"""Pydantic v2 models for structured product specifications."""

from typing import Any

from pydantic import BaseModel, Field


class LaptopSpecs(BaseModel):
    """Laptop technical specifications model."""

    processor: str | None = Field(default=None, description="CPU Model e.g. Intel Core i7-13700H")
    ram_gb: int | None = Field(default=None, ge=1, le=512, description="RAM in GB")
    ram_type: str | None = Field(default=None, description="DDR4, DDR5, LPDDR5X")
    storage_gb: int | None = Field(default=None, ge=16, le=16000, description="Storage size in GB")
    storage_type: str | None = Field(default=None, description="NVMe SSD, SATA SSD, eMMC")
    screen_size_inches: float | None = Field(
        default=None, ge=7.0, le=24.0, description="Display size in inches"
    )
    display_resolution: str | None = Field(
        default=None, description="Screen resolution e.g. 2560x1600"
    )
    gpu: str | None = Field(default=None, description="GPU Model e.g. NVIDIA RTX 4070")
    operating_system: str | None = Field(default=None, description="OS e.g. Windows 11 Home, macOS")
    weight_kg: float | None = Field(
        default=None, ge=0.3, le=10.0, description="Laptop weight in KG"
    )
    battery_capacity_wh: float | None = Field(
        default=None, ge=10.0, le=150.0, description="Battery capacity in Watt-Hours"
    )
    extra_specs: dict[str, Any] = Field(
        default_factory=dict, description="Additional arbitrary specification key-values"
    )


class MobileSpecs(BaseModel):
    """Mobile phone technical specifications model."""

    processor: str | None = Field(default=None, description="SoC Model e.g. Snapdragon 8 Gen 3")
    ram_gb: int | None = Field(default=None, ge=1, le=64, description="RAM in GB")
    storage_gb: int | None = Field(
        default=None, ge=8, le=2048, description="Internal storage in GB"
    )
    screen_size_inches: float | None = Field(
        default=None, ge=3.0, le=10.0, description="Screen size in inches"
    )
    display_type: str | None = Field(default=None, description="OLED, AMOLED, IPS LCD")
    refresh_rate_hz: int | None = Field(
        default=None, ge=30, le=240, description="Display refresh rate in Hz"
    )
    main_camera_mp: float | None = Field(
        default=None, ge=1.0, le=200.0, description="Main camera megapixels"
    )
    selfie_camera_mp: float | None = Field(
        default=None, ge=1.0, le=100.0, description="Selfie camera megapixels"
    )
    battery_capacity_mah: int | None = Field(
        default=None, ge=500, le=20000, description="Battery capacity in mAh"
    )
    charging_wattage: float | None = Field(
        default=None, ge=1.0, le=300.0, description="Fast charging speed in Watts"
    )
    operating_system: str | None = Field(default=None, description="Android 14, iOS 17")
    extra_specs: dict[str, Any] = Field(
        default_factory=dict, description="Additional arbitrary specification key-values"
    )


class GenericProductSpecs(BaseModel):
    """Generic specs container for unclassified products."""

    attributes: dict[str, Any] = Field(default_factory=dict, description="Generic attribute map")
