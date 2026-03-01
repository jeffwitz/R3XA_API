# THIS FILE IS AUTO-GENERATED
# Source: r3xa_api/resources/schema.json
# Command: make generate-models
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Settings(RootModel[Any]):
    root: Any


class DataSources(RootModel[Any]):
    root: Any


class DataSets(RootModel[Any]):
    root: Any


class Types(RootModel[Any]):
    root: Any


class OutputDimension(Enum):
    point = 'point'
    curve = 'curve'
    surface = 'surface'
    volume = 'volume'


class DataSetFile(BaseModel):
    filename: str
    file_type: Optional[str] = Field(
        None,
        description='MIME type of the file.',
        examples=['text/csv', 'text/txt'],
        title='MIME',
    )
    delimiter: Optional[str] = Field(';', examples=[';', ',', ':', '\t'])
    data_range: Optional[str] = Field(None, examples=['B42:B421'])
    kind: Literal['data_set_file'] = Field(
        ...,
        description='Only required for specs implementation purposes',
        title='Kind of object',
    )


class DataSetId(RootModel[str]):
    root: str = Field(..., description='ID of a data set.')


class DataSourceId(RootModel[str]):
    root: str = Field(..., description='ID of a data source.')


class Uint(RootModel[int]):
    root: int = Field(..., description='Unsigned int', ge=0, title='uint')


class Unit(BaseModel):
    title: Optional[str] = Field(
        None,
        description='Title of the unit.',
        examples=['length', 'width', 'speed'],
        title='Title',
    )
    value: Optional[float] = Field(None, description='Numerical value.', title='Value')
    unit: str = Field(
        ...,
        description='Sign of the unit.',
        examples=['m', 'kN', 'kg', 'm/s'],
        title='Unit',
    )
    scale: Optional[float] = Field(
        None, description='Factor with respect to the standard system', title='Scale'
    )
    kind: Literal['unit'] = Field(
        ...,
        description='Only required for specs implementation purposes',
        title='Kind of object',
    )


class File(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data set.', title='ID')
    kind: Literal['data_sets/file'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the data set.', title='Title')
    description: str = Field(
        ..., description='Description of the data set.', title='Description'
    )
    folder: Optional[str] = Field(
        None,
        description='Relative path to the folder containing the timestamps and data file(s).',
        examples=['..', '.', 'my_folder/my_tabular.txt'],
        title='Folder',
    )
    data_sources: list[DataSourceId] = Field(
        ..., description='List of IDs of the data sources.', title='Data sources'
    )
    time_reference: float = Field(
        ...,
        description='Time serving as a reference to the whole data set.',
        title='Time reference',
    )
    keywords: Optional[list[str]] = Field(
        None, description='List of keywords.', title='Keywords'
    )
    timestamps: DataSetFile = Field(
        ..., description='Path and range to the timestamps file', title='Timestamps'
    )
    data: DataSetFile = Field(
        ..., description='Path and range to the data file', title='Data'
    )


class Generic(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data set.', title='ID')
    kind: Literal['data_sets/generic'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the data set.', title='Title')
    description: str = Field(
        ..., description='Description of the data set.', title='Description'
    )
    file_type: str = Field(
        ..., description='MIME type of the file.', examples=['text/csv'], title='MIME'
    )
    path: str = Field(
        ...,
        description='Relative path to the data file.',
        examples=['../my_values.csv', 'my_folder/my_image.tif'],
        title='Path',
    )
    data_sources: list[DataSourceId] = Field(
        ..., description='List of IDs of the data sources.', title='Data sources'
    )


class List(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data set.', title='ID')
    kind: Literal['data_sets/list'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the data set.', title='Title')
    description: str = Field(
        ..., description='Description of the data set.', title='Description'
    )
    path: Optional[str] = Field(
        None,
        description='Relative path to the data folder.',
        examples=['..', 'my_folder'],
        title='Path',
    )
    file_type: str = Field(
        ...,
        description='MIME type of the data files.',
        examples=['text/csv'],
        title='MIME',
    )
    data_sources: list[DataSourceId] = Field(
        ..., description='List if IDs of the data sources.', title='Data sources'
    )
    time_reference: Unit = Field(
        ...,
        description='Time serving as a reference to the whole data set.',
        title='Time reference',
    )
    keywords: Optional[list[str]] = Field(
        None, description='List of keywords.', title='Keywords'
    )
    timestamps: list[float] = Field(
        ..., description='List of the timestamps.', title='Timestamps'
    )
    data: list[str] = Field(..., description='List of the data files.', title='Data')


class Camera(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/camera'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the camera.', title='Title')
    description: Optional[str] = Field(
        None, description='Description of the camera.', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components or channels of the ouput data.',
        examples=['3 channels for a RVB image'],
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ..., description="should be 'surface' ", title='Output dimension'
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer name, Brand.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Camera model.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    image_size: list[Unit] = Field(
        ..., description='Size of the image length unit squared.', title='Image size'
    )
    field_of_view: Optional[list[Unit]] = Field(
        None,
        description='Size of the field of view in length unit squared.',
        title='Field of view',
    )
    image_scale: Optional[Unit] = Field(
        None,
        description='Scale of the image in pixels per length unit.',
        title='Image scale',
    )
    focal_length: Optional[Unit] = Field(
        None,
        description='Focal length of the lens in length unit.',
        title='Focal length',
    )
    lens: Optional[str] = Field(
        None, description='Lens manufacturer and model names.', title='Lens'
    )
    filter: Optional[str] = Field(
        None,
        description='Filter type, manufacturer and model.',
        title='Camera or lens filter',
    )
    aperture: Optional[str] = Field(
        None, description='Aperture of the lens, example: f/8', title='Aperture'
    )
    exposure: Optional[Unit] = Field(
        None, description='Exposure time in time unit.', title='Exposure'
    )
    standoff_distance: Optional[Unit] = Field(
        None,
        description='Distance between the camera and the sample.',
        title='Standoff distance',
    )
    uncertainty: Optional[Unit] = Field(
        None, description='Estimation of image noise.', title='Uncertainty'
    )


class DicMeasurement(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/dic_measurement'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the DIC measurement.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the DIC measurement.', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components',
        examples=['2 components of displacement in 2D-DIC, 3 in DVC and Stereo DIC'],
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description="should be 'surface' for DIC or 'volume' for DVC",
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ...,
        description='examples: pixels, voxels, length unit...',
        title='Output units',
    )
    manufacturer: Optional[str] = Field(
        None, description='Software editor.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Software version.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    subset_size: Optional[list[Unit]] = Field(
        None, description='Size of the subset length unit squared.', title='Subset size'
    )
    step_size: Optional[Unit] = Field(
        None, description='distance between two adjacent subsets', title='Step size'
    )
    mesh: Optional[str] = Field(
        None,
        description='Finite Element or BSpline mesh: filename or specimen setting id',
        title='Mesh',
    )
    image_filtering: Optional[str] = Field(
        None, description='Type of filter and kernel', title='Image filtering'
    )
    interpolant: Optional[str] = Field(
        None,
        description='Subpixel interpolation: linear, cubic spline',
        title='Interpolant',
    )
    matching_criterion: str = Field(
        ..., description='ZNSSD, ZNCC or other ...', title='Matching criterion'
    )
    shape_function: Optional[str] = Field(
        None,
        description='affine, quadratic, linear triangles TRI3 ...',
        title='Shape function',
    )
    camera_model: Optional[str] = Field(
        None, description='no, pinhole, distortions modes... ', title='Camera model'
    )
    camera_parameters: Optional[str] = Field(
        None,
        description='filename or list of parameters',
        title='Calibration parameters',
    )
    regularization_type: Optional[str] = Field(
        None,
        description='strong/weak + type: gradient, elastic...',
        title='Regularization type',
    )
    regularisation_length: Optional[Unit] = Field(
        None, description='length or weight', title='Regularization length'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='e.g. uncertainty on the output field', title='Uncertainty'
    )


class GenericModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source', title='ID')
    kind: Literal['data_sources/generic'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the data source.', title='Title')
    description: str = Field(
        ..., description='Description of the data source.', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as inputs of the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components or channels of the ouput data.',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description='must be one of: point, curve, surface or volume.',
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: str = Field(
        ...,
        description='Manufacturer, vendor or software editor.',
        title='Manufacturer',
    )
    model: str = Field(
        ..., description='Model of the source or software version.', title='Model'
    )
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )


class Identification(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/identification'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the inverse analysis.', title='Title'
    )
    description: Optional[str] = Field(
        None,
        description='Description of the identification method and parameters used.',
        title='Description',
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components',
        examples=['3 or 3 components of strains is 2D, 6 in 3D'],
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ..., description='examples: %, microdefs...', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Software name.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Software version.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    parameters: Optional[list[Unit]] = Field(
        None,
        description='constitutive, geometric, loading or numerical parameters ',
        title='Parameters',
    )
    uncertainty: Optional[Unit] = Field(
        None,
        description='estimation of identification uncertainty',
        title='Uncertainty',
    )


class Infrared(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/infrared'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: str = Field(..., description='Title of the infrared camera.', title='Title')
    description: Optional[str] = Field(
        None, description='comments and additional informations', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of channels of the ouput data',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ..., description="should be 'surface'.", title='Output dimension'
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer, Brand', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Model', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    image_size: list[Unit] = Field(
        ..., description='Size of the image length unit squared.', title='Image size'
    )
    field_of_view: Optional[list[Unit]] = Field(
        None,
        description='Size of the field of view in length unit squared.',
        title='Field of view',
    )
    image_scale: Optional[Unit] = Field(
        None,
        description='Scale of the image in pixels per length unit.',
        title='Image scale',
    )
    focal_length: Optional[Unit] = Field(
        None,
        description='Focal length of the lens in lenght unit.',
        title='Focal length',
    )
    lens: Optional[str] = Field(
        None,
        description='Camera lens manufacturer and model names.',
        title='Camera lens',
    )
    filter: Optional[str] = Field(
        None,
        description='Filter type, manufacturer and model.',
        title='Camera or lens filter',
    )
    aperture: Optional[str] = Field(
        None, description='Aperture of the lens.', examples='f/8', title='Aperture'
    )
    exposure: Optional[Unit] = Field(
        None, description='Exposure time in time unit.', title='Exposure'
    )
    standoff_distance: Optional[Unit] = Field(
        None,
        description='Standoff distance between the camera and the sample in length unit.',
        title='Standoff distance',
    )
    bandwidth: list[Unit] = Field(
        ..., description='Bandwidth [item0, item1]', title='Bandwidth'
    )
    emissivity: Optional[Unit] = Field(
        None, description='Emissivity', title='Emissivity'
    )
    transmissivity: Optional[Unit] = Field(
        None, description='Transmissivity', title='Transmissivity'
    )
    nuc_file: Optional[str] = Field(
        None, description='Non Uniformity Correction', title='NUC file'
    )
    calibration_file: Optional[str] = Field(
        None, description='filename', title='Calibration File'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='estimation of image noise.', title='Uncertainty'
    )


class LoadCell(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/load_cell'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Load cell name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of the load cell', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components of the ouput data, example 1 for single axis or 6 for 6-axis sensors',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ..., description="should be 'point'", title='Output dimension'
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer, vendor, brand.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Model.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    type: Optional[str] = Field(
        None,
        description='(e.g. wheatstone, piezzo-electric, FSR).',
        title='Load cell type',
    )
    capacity: Unit = Field(
        ..., description='Capacity of the load cell / Force range.', title='Capacity'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='Quantification of data uncertainty.', title='Uncertainty'
    )


class MechanicalAnalysis(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/mechanical_analysis'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the data analysis.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the mechanical model.', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components',
        examples=['3 or 3 components of strains is 2D, 6 in 3D'],
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ..., description='examples: %, microdefs...', title='Output units'
    )
    manufacturer: str = Field(..., description='Software name.', title='Manufacturer')
    model: Optional[str] = Field(None, description='Software version.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    parameters: Optional[list[Unit]] = Field(
        None,
        description='constitutive, geometric, loading or numerical parameters ',
        title='Parameters',
    )
    uncertainty: Optional[Unit] = Field(
        None, description='estimation of numerical errors', title='Uncertainty'
    )


class PointTemperature(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/point_temperature'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Thermometer name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of thermometer', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components of the ouput data, should be 1',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ..., description="should be 'point'", title='Output dimension'
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None,
        description='Manufacturer, vendor or software editor.',
        title='Manufacturer',
    )
    model: Optional[str] = Field(
        None, description='Model or software version.', title='Model'
    )
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    range: list[Unit] = Field(
        ..., description='Temperature range [item0, item1]', title='Range'
    )
    emissivity: Optional[Unit] = Field(
        None, description='Pyrometer emissivity', title='Emissivity'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='uncertainty or resolution.', title='Uncertainty'
    )


class StrainComputation(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/strain_computation'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the data analysis.', title='Title'
    )
    description: Optional[str] = Field(
        None,
        description='Additional description of the way strains are computed from displacements.',
        title='Description',
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components',
        examples=['3 or 3 components of strains is 2D, 6 in 3D'],
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ..., description='examples: %, microdefs...', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Software name.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Software version.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    virtual_strain_gauge_size: Unit = Field(
        ..., description=' ', title='Virtual Strain Gauge size'
    )
    displacement_filtering: Optional[str] = Field(
        None,
        description='Type of filter and kernel',
        title='Displacement pre-filtering',
    )
    strain_filtering: Optional[str] = Field(
        None, description='Type of filter and kernel', title='Strain filtering'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='estimation of uncertainty on the output', title='Uncertainty'
    )


class StrainGauge(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/strain_gauge'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Strain gauge name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of the load cell', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of components of the ouput data, example: 1 or 3 for rosette.',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ..., description="should be 'point'", title='Output dimension'
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer, Vendor or brand.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Model.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    length: Unit = Field(..., description='Gauge or measuring length', title='Length')
    uncertainty: Optional[Unit] = Field(
        None, description='Uncertainty or resolution of strain.', title='Uncertainty'
    )


class Tomograph(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the data source.', title='ID')
    kind: Literal['data_sources/tomograph'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the tomograph.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the tomograph.', title='Description'
    )
    input_data_sets: Optional[list[DataSetId]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Uint = Field(
        ...,
        description='Number of channels of the ouput data.',
        title='Output components',
    )
    output_dimension: OutputDimension = Field(
        ...,
        description="should be 'surface' for radios or 'volume' for scans.",
        title='Output dimension',
    )
    output_units: list[Unit] = Field(
        ..., description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None,
        description='Manufacturer, vendor or software editor.',
        title='Manufacturer',
    )
    model: Optional[str] = Field(
        None, description='Model or software version.', title='Model'
    )
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    image_size: list[Unit] = Field(
        ..., description='Size of the image pixels.', title='Image size'
    )
    field_of_view: Optional[list[Unit]] = Field(
        None,
        description='Size of the field of view in length unit.',
        title='Field of view',
    )
    image_scale: Optional[Unit] = Field(
        None,
        description='Scale of the image in pixels per length unit.',
        title='Image scale',
    )
    source: str = Field(..., description='Source characteristics.', title='Source')
    voltage: Optional[Unit] = Field(
        None, description='Used voltage.', examples='50 kV', title='Voltage'
    )
    current: Optional[Unit] = Field(
        None, description='electric current.', examples='200 microA', title='Current'
    )
    detector: Optional[str] = Field(
        None, description='electric current.', title='Detector'
    )
    scan_duration: Optional[Unit] = Field(
        None, description='Scan duration', title='Scan duration'
    )
    target: Optional[str] = Field(None, description='reflexion target.', title='Target')
    tube_to_detector_distance: Optional[Unit] = Field(
        None,
        description='Distance between the tube and the detector.',
        title='Tube to detector distance',
    )
    source_to_object_distance: Optional[Unit] = Field(
        None,
        description='Distance between the source and the object.',
        title='Source to object distance',
    )
    number_of_projections: Optional[Uint] = Field(
        None, description='number of radiographs.', title='Number of projections'
    )
    angular_amplitude: Optional[Unit] = Field(
        None, description='amplitude in degree, example: 360', title='Angular amplitude'
    )
    aquisition_param_file: Optional[str] = Field(
        None, description='filename', title='Acquisition parameters file'
    )
    reconstruction_param_file: Optional[str] = Field(
        None, description='filename', title='Reconstruction parameters file'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='estimation of image noise or artifacts.', title='Uncertainty'
    )


class GenericModel1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the setting.', title='ID')
    kind: Literal['settings/generic'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: str = Field(..., description='Title of the setting.', title='Title')
    description: str = Field(
        ..., description='Description of the setting.', title='Description'
    )
    Documentation: Optional[str] = Field(
        None,
        description='Path to external documentation/information',
        title='Documentation',
    )
    associated_data_sources: Optional[list[DataSourceId]] = Field(
        None,
        description='List of datasources linked to this setting',
        title='Associated Data Sources',
    )


class Specimen(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the setting.', title='ID')
    kind: Literal['settings/specimen'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: str = Field(..., description='Title of the specimen.', title='Title')
    description: str = Field(
        ..., description='Description of the specimen.', title='Description'
    )
    cad: Optional[str] = Field(
        None,
        description='Path to the design of the specimen.',
        examples=['my-specimen.vtk'],
        title='CAD',
    )
    sizes: list[Unit] = Field(..., description='Sizes of the specimen.', title='Sizes')
    patterning_technique: Optional[str] = Field(
        None,
        description='Patterning technique used on the specimen.',
        examples=['Base coat of white spray paint with ink stamped speckles'],
        title='Patterning technique',
    )
    patterning_feature_size: Optional[Unit] = Field(
        None,
        description='Characteristic size of the pattern.',
        title='Patterning feature size',
    )


class Stereorig(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the setting.', title='ID')
    kind: Literal['settings/stereorig'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: str = Field(..., description='Title of the stereo rig.', title='Title')
    description: str = Field(
        ..., description='Description of the stereo rig.', title='Description'
    )
    stereo_angle: Unit = Field(
        ..., description='Stereo angle between the camera axes.', title='Stereo Angle'
    )
    calibration_target_type: Optional[str] = Field(
        None,
        description='Type of calibration board.',
        examples=[
            '(a)symmetric Circle Grid',
            'Checkerboard',
            'ChArUco',
            'AprilTag Grid',
            'Pattern',
            'Custom',
        ],
        title='Calibration Target type',
    )
    calibration_target_size: Optional[list[Unit]] = Field(
        None,
        description='Parameters of the calibration board.',
        title='Calibration Target size',
    )
    associated_data_sources: Optional[list[DataSourceId]] = Field(
        None, description='List of cameras of the rig', title='Associated Data Sources'
    )


class TestingMachine(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: str = Field(..., description='ID of the setting.', title='ID')
    kind: Literal['settings/testing_machine'] = Field(
        ...,
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: str = Field(..., description='Title of the testing machine.', title='Title')
    description: str = Field(
        ..., description='Description of the testing machine.', title='Description'
    )
    type: str = Field(
        ...,
        description='e.g. compression, tensile, torsion, fatigue...',
        title='Type of machine',
    )
    manufacturer: Optional[str] = Field(
        None,
        description='Manufacturer, vendor or software editor.',
        title='Manufacturer',
    )
    model: Optional[str] = Field(
        None, description='Model of the source or software version.', title='Model'
    )
    documentation: Optional[str] = Field(
        None, description='filename', title='Documentation'
    )
    capacity: Optional[Uint] = Field(
        None, description='load capacity', title='Capacity'
    )
    associated_data_sources: Optional[list[DataSourceId]] = Field(
        None,
        description='List of associated sources (extensometers, load cells)',
        title='Associated Data Sources',
    )


class R3XADocument(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    title: str = Field(
        ...,
        description='Title of the data sets.',
        examples=[['DICComposite2.0', 'My awesome data sets']],
        title='Title',
    )
    description: str = Field(
        ..., description='Description of the data sets.', title='Description'
    )
    version: Literal['2024.7.1'] = Field(
        ..., description='Version of the schema used.', title='Version'
    )
    authors: str = Field(
        ...,
        description='Names, ORCID, IDHAL...',
        examples=['M. Palin, J. Cleese', 'ORCID', 'HAL-ID'],
        title='Author',
    )
    date: str = Field(
        ...,
        description='Global date of the experiment (YYYY-MM-DD).',
        examples=['2020-03-17'],
        pattern='^[1-2]{1}[0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$',
        title='Date',
    )
    repository: Optional[str] = Field(
        None,
        description='URL to the repository where the dataset is stored.',
        examples=['https://zenodo.org/records/42'],
        title='Repository',
    )
    documentation: Optional[str] = Field(
        None,
        description='URI to the documentation (pdf)',
        examples=['./doc/my_doc.pdf', 'https://zenodo.org/records/42/doc/my_doc.pdf'],
        title='Documentation',
    )
    license: Optional[str] = Field(
        None,
        description='Public domain, CC-BY, ...',
        examples=['Creative common'],
        title='License',
    )
    settings: Optional[
        list[Union[GenericModel1, Specimen, TestingMachine, Stereorig]]
    ] = Field(
        None,
        description='Experimental parameters should be the specimen, patterning technique and machines used (light, testing rig, environmental chamber...). Describe the experimental techniques/apparatus and devices used / light / environment chamber...',
        title='Settings',
    )
    data_sources: Optional[
        list[
            Union[
                GenericModel,
                Camera,
                Infrared,
                Tomograph,
                LoadCell,
                StrainGauge,
                PointTemperature,
                DicMeasurement,
                MechanicalAnalysis,
                Identification,
                StrainComputation,
            ]
        ]
    ] = Field(
        None,
        description='A data source is a procedure or a system that generates a data set. If it is a sensor then its parameters must be specified. If it is an analysis, its parameters are specified along with the input parameters. It also indicates the dimension, the number of components and the unit of the output data.',
        title='Data sources',
    )
    data_sets: Optional[list[Union[Generic, File, List]]] = Field(
        None,
        description='A data set gives the organisation of the measured or generated data and time resolution.',
        title='Data sets',
    )

# --- stable typed aliases (auto-generated) ---
CameraSource = Camera
GenericSource = GenericModel
SpecimenSetting = Specimen
GenericSetting = GenericModel1
ImageSetList = List
ImageSetFile = File
GenericDataSet = Generic

__all__ = [
    'Unit',
    'DataSetFile',
    'CameraSource',
    'GenericSource',
    'SpecimenSetting',
    'GenericSetting',
    'ImageSetList',
    'ImageSetFile',
    'GenericDataSet',
    'R3XADocument',
]
# --- end stable typed aliases ---
