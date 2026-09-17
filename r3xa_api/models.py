# THIS FILE IS AUTO-GENERATED
# Source: r3xa_api/resources/schema.json
# Command: python scripts/dev.py generate-models
# DO NOT EDIT MANUALLY

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import ConfigDict, Field, RootModel

from r3xa_api.model_base import R3XAItem


class Settings(RootModel[Optional[Any]]):
    root: Optional[Any] = None


class DataSources(RootModel[Optional[Any]]):
    root: Optional[Any] = None


class DataSets(RootModel[Optional[Any]]):
    root: Optional[Any] = None


class Types(RootModel[Optional[Any]]):
    root: Optional[Any] = None


class DataOrigin(Enum):
    raw = 'raw'
    derived = 'derived'


class OutputDimension(Enum):
    point = 'point'
    curve = 'curve'
    surface = 'surface'
    volume = 'volume'


class Author(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    name: Optional[str] = Field(
        None, description='Full name of the author.', min_length=1, title='Name'
    )
    affiliation: Optional[str] = Field(
        None,
        description='Institution the author belongs to.',
        min_length=1,
        title='Affiliation',
    )
    orcid: Optional[str] = Field(
        None, description='ORCID identifier of the author.', min_length=1, title='ORCID'
    )


class Col(RootModel[Optional[int]]):
    root: Optional[int] = Field(
        None,
        description='Non-negative index (0-based) or non-empty name of the column containing the data.',
        ge=0,
        title='Column',
    )


class Col1(RootModel[Optional[str]]):
    root: Optional[str] = Field(
        None,
        description='Non-negative index (0-based) or non-empty name of the column containing the data.',
        min_length=1,
        title='Column',
    )


class Row(RootModel[Optional[int]]):
    root: Optional[int] = Field(None, ge=0)


class Row1(RootModel[Optional[int]]):
    root: Optional[int] = Field(None, ge=0)


class DataSetFile(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    filename: Optional[str] = None
    file_type: Optional[str] = Field(
        None,
        description='MIME type of the (CSV-like) file containing the data.',
        title='MIME type',
    )
    delimiter: Optional[str] = ';'
    col: Optional[Union[Col, Col1]] = Field(
        None,
        description='Non-negative index (0-based) or non-empty name of the column containing the data.',
        title='Column',
    )
    rows: Optional[tuple[Row, Optional[Row1]]] = Field(
        None,
        description='Range of rows containing the data, header excluded (0-based), expressed as [first_row, last_row]. Both bounds are inclusive; set last_row to null to read through the end of the file.',
        title='Rows',
    )
    kind: Literal['data_set_file'] = Field(
        'data_set_file',
        description='Only required for specs implementation purposes',
        title='Kind of object',
    )


class DataSetId(RootModel[Optional[str]]):
    root: Optional[str] = Field(
        None,
        description='ID of a data set. Identifiers share one flat namespace: a prefix such as `stg-` / `src-` / `set-` keeps them unambiguous.',
    )


class DataSourceId(RootModel[Optional[str]]):
    root: Optional[str] = Field(
        None,
        description='ID of a data source. Identifiers share one flat namespace: a prefix such as `stg-` / `src-` / `set-` keeps them unambiguous.',
    )


class SettingId(RootModel[Optional[str]]):
    root: Optional[str] = Field(
        None,
        description='ID of a setting. Identifiers share one flat namespace: a prefix such as `stg-` / `src-` / `set-` keeps them unambiguous.',
    )


# Object-first references accept either a wire ID or an in-memory R3XA object.
DataSourceReference = Union[DataSourceId, R3XAItem]
DataSetReference = Union[DataSetId, R3XAItem]
SettingReference = Union[SettingId, R3XAItem]

class Uint(RootModel[Optional[int]]):
    root: Optional[int] = Field(None, description='Unsigned int', ge=0, title='uint')


class Unit(R3XAItem):
    title: Optional[str] = Field(None, description='Title of the unit.', title='Title')
    value: Optional[float] = Field(None, description='Numerical value.', title='Value')
    unit: Optional[str] = Field(None, description='Sign of the unit.', title='Unit')
    scale: Optional[float] = Field(
        None, description='Factor with respect to the standard system', title='Scale'
    )
    kind: Literal['unit'] = Field(
        'unit',
        description='Only required for specs implementation purposes',
        title='Kind of object',
    )


class File(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data set.', title='ID')
    kind: Literal['data_sets/file'] = Field(
        'data_sets/file',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the data set.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the data set.', title='Description'
    )
    path: Optional[str] = Field(
        None,
        description='Relative path to the folder containing the data file(s).',
        title='Path',
    )
    parent_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List of IDs of the data sources that generated the dataset.',
        title='Parent data sources',
    )
    data_type: Optional[str] = Field(
        None,
        description="if the CSV contains numbers > data_type should be 'numbers', if it contains filenames > put the MIME type",
        title='Data type',
    )
    time_reference: Optional[Unit] = Field(
        None,
        description='Time serving as a reference to the whole data set.',
        title='Time reference',
    )
    keywords: Optional[list[str]] = Field(
        None, description='List of keywords.', title='Keywords'
    )
    timestamps: Optional[DataSetFile] = Field(
        None,
        description='filename (ex: CSV) + col and rows where to find the timestamps',
        title='Timestamps',
    )
    values: Optional[DataSetFile] = Field(
        None,
        description='filename (ex: CSV) + col and rows where to find the files or values',
        title='Data set file',
    )
    data_origin: Optional[DataOrigin] = Field(
        None,
        description='Whether the data set holds raw measurements or the result of an analysis.',
        title='Data origin',
    )


class Generic(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data set.', title='ID')
    kind: Literal['data_sets/generic'] = Field(
        'data_sets/generic',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the data set.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the data set.', title='Description'
    )
    data_type: Optional[str] = Field(
        None, description='MIME type of the listed files.', title='MIME'
    )
    path: Optional[str] = Field(
        None,
        description='Relative path to the folder containing the data file(s).',
        title='Path',
    )
    parent_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List of IDs of the data sources that generated the dataset.',
        title='Parent data sources',
    )
    data_origin: Optional[DataOrigin] = Field(
        None,
        description='Whether the data set holds raw measurements or the result of an analysis.',
        title='Data origin',
    )


class List(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data set.', title='ID')
    kind: Literal['data_sets/list'] = Field(
        'data_sets/list',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the data set.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the data set.', title='Description'
    )
    path: Optional[str] = Field(
        None, description='Relative path to the data folder.', title='Path'
    )
    data_type: Optional[str] = Field(
        None, description='MIME type of the listed data files.', title='MIME'
    )
    parent_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List if IDs of the data sources that generated the dataset.',
        title='Parent data sources',
    )
    time_reference: Optional[Unit] = Field(
        None,
        description='Time serving as a reference to the whole data set.',
        title='Time reference',
    )
    keywords: Optional[list[str]] = Field(
        None, description='List of keywords.', title='Keywords'
    )
    timestamps: Optional[list[float]] = Field(
        None, description='List of the timestamps.', title='Timestamps'
    )
    values: Optional[list[str]] = Field(
        None, description='List of strings.', title='List of files'
    )
    data_origin: Optional[DataOrigin] = Field(
        None,
        description='Whether the data set holds raw measurements or the result of an analysis.',
        title='Data origin',
    )


class Camera(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/camera'] = Field(
        'data_sources/camera',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the camera.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the camera.', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of components or channels of the ouput data.',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None, description="should be 'surface' ", title='Output dimension'
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer name, Brand.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Camera model.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    image_size: Optional[list[Unit]] = Field(
        None, description='Size of the image length unit squared.', title='Image size'
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


class DicMeasurement(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/dic_measurement'] = Field(
        'data_sources/dic_measurement',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the DIC measurement.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the DIC measurement.', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None, description='Number of components', title='Output components'
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description="should be 'surface' for DIC or 'volume' for DVC",
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None,
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
    mesh: Optional[SettingReference] = Field(
        None,
        description='Specimen setting holding the mesh used by the analysis.',
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
    matching_criterion: Optional[str] = Field(
        None, description='ZNSSD, ZNCC or other ...', title='Matching criterion'
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


class GenericModel(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source', title='ID')
    kind: Literal['data_sources/generic'] = Field(
        'data_sources/generic',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the data source.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the data source.', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as inputs of the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of components or channels of the ouput data.',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description='must be one of: point, curve, surface or volume.',
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
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
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='Quantification of data uncertainty.', title='Uncertainty'
    )


class Identification(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/identification'] = Field(
        'data_sources/identification',
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
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None, description='Number of components', title='Output components'
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='examples: %, microdefs...', title='Output units'
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
        description='list of constitutive, geometric, loading or numerical parameters ',
        title='Parameters',
    )
    uncertainty: Optional[Unit] = Field(
        None,
        description='estimation of identification uncertainty',
        title='Uncertainty',
    )


class Infrared(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/infrared'] = Field(
        'data_sources/infrared',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the infrared camera.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='comments and additional informations', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of channels of the ouput data',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None, description="should be 'surface'.", title='Output dimension'
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer, Brand', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Model', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    image_size: Optional[list[Unit]] = Field(
        None, description='Size of the image length unit squared.', title='Image size'
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
        None, description='Aperture of the lens.', title='Aperture'
    )
    exposure: Optional[Unit] = Field(
        None, description='Exposure time in time unit.', title='Exposure'
    )
    standoff_distance: Optional[Unit] = Field(
        None,
        description='Standoff distance between the camera and the sample in length unit.',
        title='Standoff distance',
    )
    bandwidth: Optional[list[Unit]] = Field(
        None, description='Bandwidth [item0, item1]', title='Bandwidth'
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


class LoadCell(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/load_cell'] = Field(
        'data_sources/load_cell',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Load cell name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of the load cell', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of components of the ouput data, example 1 for single axis or 6 for 6-axis sensors',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None, description="should be 'point'", title='Output dimension'
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
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
    capacity: Optional[Unit] = Field(
        None, description='Capacity of the load cell / Force range.', title='Capacity'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='Quantification of data uncertainty.', title='Uncertainty'
    )


class MechanicalAnalysis(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/mechanical_analysis'] = Field(
        'data_sources/mechanical_analysis',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Name of the data analysis.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the mechanical model.', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None, description='Number of components', title='Output components'
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='examples: %, microdefs...', title='Output units'
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
        description='list of constitutive, geometric, loading or numerical parameters ',
        title='Parameters',
    )
    uncertainty: Optional[Unit] = Field(
        None, description='estimation of numerical errors', title='Uncertainty'
    )


class PointTemperature(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/point_temperature'] = Field(
        'data_sources/point_temperature',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Thermometer name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of thermometer', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of components of the ouput data, should be 1',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None, description="should be 'point'", title='Output dimension'
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
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
    range: Optional[list[Unit]] = Field(
        None, description='Temperature range [item0, item1]', title='Range'
    )
    emissivity: Optional[Unit] = Field(
        None, description='Pyrometer emissivity', title='Emissivity'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='uncertainty or resolution.', title='Uncertainty'
    )


class StrainComputation(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/strain_computation'] = Field(
        'data_sources/strain_computation',
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
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None, description='Number of components', title='Output components'
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description="should be 'surface' for 2D or 'volume' for 3D",
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='examples: %, microdefs...', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Software name.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Software version.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    virtual_strain_gauge_size: Optional[Unit] = Field(
        None, description=' ', title='Virtual Strain Gauge size'
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


class StrainGauge(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/strain_gauge'] = Field(
        'data_sources/strain_gauge',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(None, description='Strain gauge name', title='Title')
    description: Optional[str] = Field(
        None, description='Description of the load cell', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of components of the ouput data, example: 1 or 3 for rosette.',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None, description="should be 'point'", title='Output dimension'
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
    )
    manufacturer: Optional[str] = Field(
        None, description='Manufacturer, Vendor or brand.', title='Manufacturer'
    )
    model: Optional[str] = Field(None, description='Model.', title='Model')
    documentation: Optional[str] = Field(
        None, description='Documentation filename, path or URL', title='Documentation'
    )
    length: Optional[Unit] = Field(
        None, description='Gauge or measuring length', title='Length'
    )
    uncertainty: Optional[Unit] = Field(
        None, description='Uncertainty or resolution of strain.', title='Uncertainty'
    )


class Tomograph(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the data source.', title='ID')
    kind: Literal['data_sources/tomograph'] = Field(
        'data_sources/tomograph',
        description='Only required for specs implementation purposes.',
        title='Kind of data source',
    )
    title: Optional[str] = Field(
        None, description='Title of the tomograph.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the tomograph.', title='Description'
    )
    input_data_sets: Optional[list[DataSetReference]] = Field(
        None,
        description='Data sets IDs serving as an input to the source.',
        title='List of the data sets',
    )
    output_components: Optional[Uint] = Field(
        None,
        description='Number of channels of the ouput data.',
        title='Output components',
    )
    output_dimension: Optional[OutputDimension] = Field(
        None,
        description="should be 'surface' for radios or 'volume' for scans.",
        title='Output dimension',
    )
    output_units: Optional[list[Unit]] = Field(
        None, description='Unit of the output data.', title='Output units'
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
    image_size: Optional[list[Unit]] = Field(
        None, description='Size of the image pixels.', title='Image size'
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
    source: Optional[str] = Field(
        None, description='Source characteristics.', title='Source'
    )
    voltage: Optional[Unit] = Field(None, description='Used voltage.', title='Voltage')
    current: Optional[Unit] = Field(
        None, description='electric current.', title='Current'
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


class GenericModel1(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the setting.', title='ID')
    kind: Literal['settings/generic'] = Field(
        'settings/generic',
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: Optional[str] = Field(
        None, description='Title of the setting.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the setting.', title='Description'
    )
    documentation: Optional[str] = Field(
        None,
        description='Path to external documentation/information',
        title='Documentation',
    )
    attached_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List of data sources equipping this device',
        title='Data Sources attached to the setting',
    )


class Specimen(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the setting.', title='ID')
    kind: Literal['settings/specimen'] = Field(
        'settings/specimen',
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: Optional[str] = Field(
        None, description='Title of the specimen.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the specimen.', title='Description'
    )
    cad: Optional[str] = Field(
        None, description='Path to the design of the specimen.', title='CAD'
    )
    mesh: Optional[str] = Field(
        None,
        description='Path to the Finite Element or BSpline mesh of the specimen.',
        title='Mesh',
    )
    sizes: Optional[list[Unit]] = Field(
        None, description='Sizes of the specimen.', title='Sizes'
    )
    patterning_technique: Optional[str] = Field(
        None,
        description='Patterning technique used on the specimen.',
        title='Patterning technique',
    )
    patterning_feature_size: Optional[Unit] = Field(
        None,
        description='Characteristic size of the pattern.',
        title='Patterning feature size',
    )


class Stereorig(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the setting.', title='ID')
    kind: Literal['settings/stereorig'] = Field(
        'settings/stereorig',
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: Optional[str] = Field(
        None, description='Title of the stereo rig.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the stereo rig.', title='Description'
    )
    stereo_angle: Optional[Unit] = Field(
        None, description='Stereo angle between the camera axes.', title='Stereo Angle'
    )
    calibration_target_type: Optional[str] = Field(
        None, description='Type of calibration board.', title='Calibration Target type'
    )
    calibration_target_size: Optional[list[Unit]] = Field(
        None,
        description='Parameters of the calibration board.',
        title='Calibration Target size',
    )
    attached_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List of data sources equipping this stereo rig',
        title='Data Sources attached to the setting',
    )


class TestingMachine(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    id: Optional[str] = Field(None, description='ID of the setting.', title='ID')
    kind: Literal['settings/testing_machine'] = Field(
        'settings/testing_machine',
        description='Only required for specs implementation purposes.',
        title='Kind of object',
    )
    title: Optional[str] = Field(
        None, description='Title of the testing machine.', title='Title'
    )
    description: Optional[str] = Field(
        None, description='Description of the testing machine.', title='Description'
    )
    type: Optional[str] = Field(
        None,
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
    capacity: Optional[Unit] = Field(
        None, description='load capacity', title='Capacity'
    )
    attached_data_sources: Optional[list[DataSourceReference]] = Field(
        None,
        description='List of data sources (extensometers, load cells) equipping this device',
        title='Data Sources attached to the setting',
    )


class R3XADocument(R3XAItem):
    model_config = ConfigDict(
        extra='forbid',
    )
    title: Optional[str] = Field(
        None,
        description='Title of the data sets.',
        examples=[['DICComposite2.0', 'My awesome data sets']],
        min_length=1,
        title='Title',
    )
    description: Optional[str] = Field(
        None,
        description='Description of the data sets.',
        min_length=1,
        title='Description',
    )
    version: Literal['2026.9.18'] = Field(
        '2026.9.18', description='Version of the schema used.', title='Version'
    )
    authors: Optional[list[Author]] = Field(
        None,
        description='Authors of the experiment or analysis.',
        min_length=1,
        title='Authors',
    )
    date: Optional[str] = Field(
        None,
        description='Global date of the experiment (YYYY-MM-DD).',
        pattern='^[1-2]{1}[0-9]{3}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$',
        title='Date',
    )
    repository: Optional[str] = Field(
        None,
        description='URL to the repository where the dataset is stored.',
        title='Repository',
    )
    documentation: Optional[str] = Field(
        None, description='URI to the documentation (pdf)', title='Documentation'
    )
    license: Optional[str] = Field(
        None, description='Public domain, CC-BY, ...', title='License'
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
R3XAModel = R3XAItem
CameraSource = Camera
GenericSource = GenericModel
InfraredSource = Infrared
TomographSource = Tomograph
LoadCellSource = LoadCell
StrainGaugeSource = StrainGauge
PointTemperatureSource = PointTemperature
DicMeasurementSource = DicMeasurement
MechanicalAnalysisSource = MechanicalAnalysis
IdentificationSource = Identification
StrainComputationSource = StrainComputation
SpecimenSetting = Specimen
GenericSetting = GenericModel1
TestingMachineSetting = TestingMachine
StereorigSetting = Stereorig
ListDataSet = List
FileDataSet = File
GenericDataSet = Generic
ImageSetList = List
ImageSetFile = File

# Legacy names from the 1.x line and the apijc branch.
SpecimenSettings = SpecimenSetting
StereorigSettings = StereorigSetting
TestingMachineSettings = TestingMachineSetting
GenericDataSource = GenericSource
CameraDataSource = CameraSource
InfraredDataSource = InfraredSource
TomographDataSource = TomographSource
LoadCellDataSource = LoadCellSource
StrainGaugeDataSource = StrainGaugeSource
PointTemperatureDataSource = PointTemperatureSource
DicMeasurementDataSource = DicMeasurementSource
MechanicalAnalysisDataSource = MechanicalAnalysisSource
IdentificationDataSource = IdentificationSource
StrainComputationDataSource = StrainComputationSource

__all__ = [
    'R3XAItem',
    'R3XAModel',
    'Unit',
    'DataSetFile',
    'OutputDimension',
    'DataSourceReference',
    'DataSetReference',
    'SettingReference',
    'R3XADocument',
    'CameraSource',
    'GenericSource',
    'InfraredSource',
    'TomographSource',
    'LoadCellSource',
    'StrainGaugeSource',
    'PointTemperatureSource',
    'DicMeasurementSource',
    'MechanicalAnalysisSource',
    'IdentificationSource',
    'StrainComputationSource',
    'SpecimenSetting',
    'GenericSetting',
    'TestingMachineSetting',
    'StereorigSetting',
    'ListDataSet',
    'FileDataSet',
    'GenericDataSet',
    'ImageSetList',
    'ImageSetFile',
    'SpecimenSettings',
    'StereorigSettings',
    'TestingMachineSettings',
    'GenericDataSource',
    'CameraDataSource',
    'InfraredDataSource',
    'TomographDataSource',
    'LoadCellDataSource',
    'StrainGaugeDataSource',
    'PointTemperatureDataSource',
    'DicMeasurementDataSource',
    'MechanicalAnalysisDataSource',
    'IdentificationDataSource',
    'StrainComputationDataSource',
]
# --- end stable typed aliases ---
