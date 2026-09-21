from __future__ import annotations

# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.
# DO NOT EDIT MANUALLY.

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union
from r3xa_api.models import (
    Author,
    CameraSource,
    DicMeasurementSource,
    FileDataSet,
    GenericDataSet,
    GenericSetting,
    GenericSource,
    IdentificationSource,
    InfraredSource,
    ListDataSet,
    LoadCellSource,
    MechanicalAnalysisSource,
    PointTemperatureSource,
    R3XADocument,
    SpecimenSetting,
    StrainComputationSource,
    StrainGaugeSource,
    StereorigSetting,
    TestingMachineSetting,
    TomographSource,
)

SettingItem = Union[GenericSetting, SpecimenSetting, TestingMachineSetting, StereorigSetting]
DataSourceItem = Union[GenericSource, CameraSource, InfraredSource, TomographSource, LoadCellSource, StrainGaugeSource, PointTemperatureSource, DicMeasurementSource, MechanicalAnalysisSource, IdentificationSource, StrainComputationSource]
DataSetItem = Union[GenericDataSet, FileDataSet, ListDataSet]

class R3XAItem:
    @property
    def kind(self) -> Optional[str]: ...
    def __getitem__(self, field: str) -> Any: ...
    def __setitem__(self, field: str, value: Any) -> None: ...
    def merge(self, **overrides: Any) -> R3XAItem: ...
    def to_dict(self, *, exclude_none: bool = ...) -> Dict[str, Any]: ...
    def to_json(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...
    def dump(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...
    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, validate: bool = ...) -> R3XAItem: ...
    def required_fields(self) -> list[str]: ...
    def optional_fields(self) -> list[str]: ...
    def missing_fields(self) -> list[str]: ...
    def field_descriptions(self) -> Dict[str, str]: ...
    def summary(self) -> str: ...
    def print(self) -> None: ...
    def validate(self, *, schema: Optional[Dict[str, Any]] = ...) -> None: ...
    @classmethod
    def load(cls, path: str | Path, *, validate: bool = ...) -> R3XAItem: ...
    @classmethod
    def loads(cls, text: str, *, validate: bool = ...) -> R3XAItem: ...
    def save(self, path: str | Path, *, validate: bool = ..., exclude_none: bool = ..., indent: Optional[int] = ...) -> Path: ...
    def plot(self, path: str | Path, *, backend: str = ..., palette: Optional[str] = ..., include_description: bool = ..., relations: str = ..., **kwargs: Any) -> Path: ...

def author(
    name: str,
    affiliation: Optional[str] = ...,
    orcid: Optional[str] = ...,
    **extra: Any,
) -> R3XAItem: ...

def new_item(kind: str, **fields: Any) -> R3XAItem: ...

def unit(
    title: Optional[str] = ...,
    value: Optional[float] = ...,
    unit: Optional[str] = ...,
    scale: Optional[float] = ...,
    **extra: Any,
) -> R3XAItem: ...

def data_set_file(
    filename: Optional[str] = ...,
    file_type: Optional[str] = ...,
    delimiter: Optional[str] = ...,
    col: Optional[int | str] = ...,
    rows: Optional[list[int | None]] = ...,
    **extra: Any,
) -> R3XAItem: ...

def new_generic_setting(
    title: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_specimen_setting(
    title: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_stereorig_setting(
    title: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_testing_machine_setting(
    title: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_camera_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_dic_measurement_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_generic_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_identification_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_infrared_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_load_cell_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_mechanical_analysis_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_point_temperature_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_strain_computation_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_strain_gauge_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_tomograph_source(
    title: Any,
    output_components: Any,
    output_dimension: Any,
    output_units: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_file_data_set(
    title: Any,
    timestamps: Any,
    values: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_generic_data_set(
    title: Any,
    parent_data_sources: Any,
    path: Any,
    **extra: Any,
) -> R3XAItem: ...

def new_list_data_set(
    title: Any,
    timestamps: Any,
    values: Any,
    **extra: Any,
) -> R3XAItem: ...

class R3XAFile(R3XADocument):
    header: Dict[str, Any]
    title: Optional[str]
    description: Optional[str]
    version: Optional[str]
    authors: Optional[list[Author]]
    date: Optional[str]
    repository: Optional[str]
    documentation: Optional[str]
    license: Optional[str]
    settings: list[SettingItem]
    data_sources: list[DataSourceItem]
    data_sets: list[DataSetItem]

    def __init__(self, **data: Any) -> None: ...

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, validate: bool = ...) -> R3XAFile: ...

    @classmethod
    def load(cls, path: str | Path, *, validate: bool = ...) -> R3XAFile: ...

    @classmethod
    def from_model(cls, model: R3XADocument) -> R3XAFile: ...

    @classmethod
    def loads(cls, text: str, *, validate: bool = ...) -> R3XAFile: ...

    def set_header(self, **fields: Any) -> R3XAFile: ...

    def add_item(self, item: Any = ..., *, section: Optional[str] = ..., **fields: Any) -> R3XAItem: ...
    def add_setting(self, item: Any = ..., **fields: Any) -> R3XAItem: ...
    def add_data_source(self, item: Any = ..., **fields: Any) -> R3XAItem: ...
    def add_data_set(self, item: Any = ..., **fields: Any) -> R3XAItem: ...
    def find(self, item_id: str) -> Optional[R3XAItem]: ...
    @classmethod
    def required_fields(cls) -> list[str]: ...
    @classmethod
    def optional_fields(cls) -> list[str]: ...
    def missing_fields(self) -> list[str]: ...
    @classmethod
    def field_descriptions(cls) -> Dict[str, str]: ...

    # Guided setting helpers
    def add_generic_setting(
        self,
        title: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_specimen_setting(
        self,
        title: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_stereorig_setting(
        self,
        title: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_testing_machine_setting(
        self,
        title: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    # Guided data source helpers
    def add_camera_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_dic_measurement_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_generic_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_identification_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_infrared_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_load_cell_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_mechanical_analysis_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_point_temperature_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_strain_computation_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_strain_gauge_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_tomograph_source(
        self,
        title: Any,
        output_components: Any,
        output_dimension: Any,
        output_units: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    # Guided data set helpers
    def add_file_data_set(
        self,
        title: Any,
        timestamps: Any,
        values: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_generic_data_set(
        self,
        title: Any,
        parent_data_sources: Any,
        path: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def add_list_data_set(
        self,
        title: Any,
        timestamps: Any,
        values: Any,
        **extra: Any,
    ) -> R3XAItem: ...

    def to_dict(self) -> Dict[str, Any]: ...
    def validate(self) -> None: ...
    def to_model(self) -> R3XAFile: ...
    def dump(self, *, exclude_none: bool = ..., indent: Optional[int] = ...) -> str: ...
    def save(self, path: str | Path, *, validate: bool = ..., exclude_none: bool = ..., indent: Optional[int] = ...) -> Path: ...
    def summary(self) -> str: ...
    def print(self) -> None: ...
    def plot(
        self,
        path: str | Path,
        *,
        backend: str = ...,
        palette: str | None = ...,
        include_description: bool = ...,
        relations: str = ...,
        **kwargs: Any,
    ) -> Path: ...
