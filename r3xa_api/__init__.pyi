from __future__ import annotations

# AUTO-GENERATED FROM THE ACTIVE R3XA SCHEMA.
# DO NOT EDIT MANUALLY.

from typing import Any

from . import models
from .core import R3XAFile, R3XAItem, author, data_set_file, new_item, unit
from .core import (
    new_camera_source,
    new_dic_measurement_source,
    new_file_data_set,
    new_generic_data_set,
    new_generic_setting,
    new_generic_source,
    new_identification_source,
    new_infrared_source,
    new_list_data_set,
    new_load_cell_source,
    new_mechanical_analysis_source,
    new_point_temperature_source,
    new_specimen_setting,
    new_stereorig_setting,
    new_strain_computation_source,
    new_strain_gauge_source,
    new_testing_machine_setting,
    new_tomograph_source,
)
from .models import (
    R3XAModel,
    Unit,
    DataSetFile,
    OutputDimension,
    DataSourceReference,
    DataSetReference,
    SettingReference,
    R3XADocument,
    CameraSource,
    GenericSource,
    InfraredSource,
    TomographSource,
    LoadCellSource,
    StrainGaugeSource,
    PointTemperatureSource,
    DicMeasurementSource,
    MechanicalAnalysisSource,
    IdentificationSource,
    StrainComputationSource,
    SpecimenSetting,
    GenericSetting,
    TestingMachineSetting,
    StereorigSetting,
    ListDataSet,
    FileDataSet,
    GenericDataSet,
    ImageSetList,
    ImageSetFile,
    SpecimenSettings,
    StereorigSettings,
    TestingMachineSettings,
    GenericDataSource,
    CameraDataSource,
    InfraredDataSource,
    TomographDataSource,
    LoadCellDataSource,
    StrainGaugeDataSource,
    PointTemperatureDataSource,
    DicMeasurementDataSource,
    MechanicalAnalysisDataSource,
    IdentificationDataSource,
    StrainComputationDataSource,
)
from .registry import (
    Registry,
    RegistryItem,
    load_item,
    load_item_path,
    load_registry,
    merge_item,
    save_item,
    save_item_path,
    validate_item,
)
from .schema import load_schema, schema_version
from .typed import from_model
from .validate import integrity_errors, validate, validate_integrity

typed_available: bool
