from __future__ import annotations

# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.
# DO NOT EDIT MANUALLY.

from pathlib import Path
from typing import Any, Dict, Optional

def new_item(kind: str, **fields: Any) -> Dict[str, Any]: ...

def unit(
    title: Optional[str] = ...,
    value: Optional[float] = ...,
    unit: Optional[str] = ...,
    scale: Optional[float] = ...,
    **extra: Any,
) -> Dict[str, Any]: ...

def data_set_file(
    filename: str,
    delimiter: Optional[str] = ...,
    data_range: Optional[str] = ...,
    **extra: Any,
) -> Dict[str, Any]: ...

class R3XAFile:
    header: Dict[str, Any]
    settings: list[Dict[str, Any]]
    data_sources: list[Dict[str, Any]]
    data_sets: list[Dict[str, Any]]

    def __init__(self, version: Optional[str] = ..., **header: Any) -> None: ...

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> R3XAFile: ...

    @classmethod
    def load(cls, path: str | Path) -> R3XAFile: ...

    @classmethod
    def loads(cls, text: str) -> R3XAFile: ...

    def set_header(self, **fields: Any) -> R3XAFile: ...

    def add_item(self, kind: str, **fields: Any) -> Dict[str, Any]: ...
    def add_setting(self, kind: str, **fields: Any) -> Dict[str, Any]: ...
    def add_data_source(self, kind: str, **fields: Any) -> Dict[str, Any]: ...
    def add_data_set(self, kind: str, **fields: Any) -> Dict[str, Any]: ...

    # Guided setting helpers
    def add_generic_setting(
        self,
        title: Any,
        description: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_specimen_setting(
        self,
        title: Any,
        description: Any,
        sizes: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_stereorig_setting(
        self,
        title: Any,
        description: Any,
        stereo_angle: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_testing_machine_setting(
        self,
        title: Any,
        description: Any,
        type: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    # Guided data source helpers
    def add_camera_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        image_size: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_dic_measurement_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        matching_criterion: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_generic_source(
        self,
        title: Any,
        description: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        manufacturer: Any,
        model: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_identification_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_infrared_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        image_size: Any,
        bandwidth: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_load_cell_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        capacity: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_mechanical_analysis_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        manufacturer: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_point_temperature_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        range: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_strain_computation_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        virtual_strain_gauge_size: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_strain_gauge_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        length: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_tomograph_source(
        self,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        image_size: Any,
        source: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    # Guided data set helpers
    def add_file_data_set(
        self,
        title: Any,
        description: Any,
        data_sources: Any,
        time_reference: Any,
        timestamps: Any,
        data: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_generic_data_set(
        self,
        title: Any,
        description: Any,
        data_sources: Any,
        file_type: Any,
        path: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_list_data_set(
        self,
        title: Any,
        description: Any,
        file_type: Any,
        data_sources: Any,
        time_reference: Any,
        timestamps: Any,
        data: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    # Legacy guided helper aliases
    def add_image_set_list(
        self,
        title: Any,
        description: Any,
        file_type: Any,
        data_sources: Any,
        time_reference: Any,
        timestamps: Any,
        data: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def add_image_set_file(
        self,
        title: Any,
        description: Any,
        data_sources: Any,
        time_reference: Any,
        timestamps: Any,
        data: Any,
        **extra: Any,
    ) -> Dict[str, Any]: ...

    def to_dict(self) -> Dict[str, Any]: ...
    def validate(self) -> None: ...
    def dump(self, indent: int = ...) -> str: ...
    def save(self, path: str | Path, indent: int = ..., validate: bool = ...) -> Path: ...
