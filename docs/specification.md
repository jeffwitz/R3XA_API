<!-- THIS FILE IS AUTO-GENERATED -->
<!-- Source: r3xa_api/resources/schema.json -->
<!-- Command: make generate-spec -->
<!-- DO NOT EDIT MANUALLY -->

# R3XA Specification

> Version : `2024.7.1`

Yet another metadata file format whose goal is to provide a data representation scheme compatible with the variety of data types encountered in experimental and computational photomechanics, and to provide a convenient framework for software coupling and data fusion.

## General Structure

| Section | Description |
|---|---|
| `header` | Top-level metadata fields (`title`, `description`, `version`, authorship and links). |
| `settings` | Experimental setup and specimen metadata. |
| `data_sources` | Sensors and processing blocks that produce data. |
| `data_sets` | Data containers linked to one or more data sources. |

## Header

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | ✅ | Title of the data sets. |
| `description` | string | ✅ | Description of the data sets. |
| `version` | "2024.7.1" (fixed) | ✅ | Version of the schema used. |
| `authors` | string | ✅ | Names, ORCID, IDHAL... |
| `date` | string | ✅ | Global date of the experiment (YYYY-MM-DD). |
| `repository` | string |  | URL to the repository where the dataset is stored. |
| `documentation` | string |  | URI to the documentation (pdf) |
| `license` | string |  | Public domain, CC-BY, ... |

## Settings

Experimental parameters should be the specimen, patterning technique and machines used (light, testing rig, environmental chamber...). Describe the experimental techniques/apparatus and devices used / light / environment chamber...

Allowed item kinds: Generic \| Specimen \| Testing Machine \| Stereorig

### Generic experimental setup (`settings/generic`)

Generic setup: testing device, environmental chamber, lights...

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the setting. |
| `kind` | "settings/generic" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the setting. |
| `description` | string | ✅ | Description of the setting. |
| `Documentation` | string |  | Path to external documentation/information |
| `associated_data_sources` | array[Data source id] |  | List of datasources linked to this setting |

### Specimen (`settings/specimen`)

Specimen.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the setting. |
| `kind` | "settings/specimen" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the specimen. |
| `description` | string | ✅ | Description of the specimen. |
| `cad` | string |  | Path to the design of the specimen. |
| `sizes` | array[<a href="#unit">Unit</a>] | ✅ | Sizes of the specimen. |
| `patterning_technique` | string |  | Patterning technique used on the specimen. |
| `patterning_feature_size` | <a href="#unit">Unit</a> |  | Characteristic size of the pattern. |

### Stereo rig (`settings/stereorig`)

Multicamera stereo rig.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the setting. |
| `kind` | "settings/stereorig" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the stereo rig. |
| `description` | string | ✅ | Description of the stereo rig. |
| `stereo_angle` | <a href="#unit">Unit</a> | ✅ | Stereo angle between the camera axes. |
| `calibration_target_type` | string |  | Type of calibration board. |
| `calibration_target_size` | array[<a href="#unit">Unit</a>] |  | Parameters of the calibration board. |
| `associated_data_sources` | array[Data source id] |  | List of cameras of the rig |

### Testing machine (`settings/testing_machine`)

any type of testing machine.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the setting. |
| `kind` | "settings/testing_machine" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the testing machine. |
| `description` | string | ✅ | Description of the testing machine. |
| `type` | string | ✅ | e.g. compression, tensile, torsion, fatigue... |
| `manufacturer` | string |  | Manufacturer, vendor or software editor. |
| `model` | string |  | Model of the source or software version. |
| `documentation` | string |  | filename |
| `capacity` | unsigned integer |  | load capacity |
| `associated_data_sources` | array[Data source id] |  | List of associated sources (extensometers, load cells) |


## Data Sources

A data source is a procedure or a system that generates a data set. If it is a sensor then its parameters must be specified. If it is an analysis, its parameters are specified along with the input parameters. It also indicates the dimension, the number of components and the unit of the output data.

Allowed item kinds: Generic \| Camera \| Infrared \| Tomograph \| Load Cell \| Strain Gauge \| Point Temperature \| Dic Measurement \| Mechanical Analysis \| Identification \| Strain Computation

### Generic data source (`data_sources/generic`)

A data source is a procedure or a system that generates a data set. If it is a sensor then his parameters must be specified. If it is an analysis specifies his parameters are specified along with the input parameters. It also indicates the dimension, the number of components and the unit of the output data.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source |
| `kind` | "data_sources/generic" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the data source. |
| `description` | string | ✅ | Description of the data source. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as inputs of the source. |
| `output_components` | unsigned integer | ✅ | Number of components or channels of the ouput data. |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | must be one of: point, curve, surface or volume. |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string | ✅ | Manufacturer, vendor or software editor. |
| `model` | string | ✅ | Model of the source or software version. |
| `documentation` | string |  | Documentation filename, path or URL |

### Visible Camera (`data_sources/camera`)

Generic camera in visible range.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/camera" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the camera. |
| `description` | string |  | Description of the camera. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components or channels of the ouput data. |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface'  |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer name, Brand. |
| `model` | string |  | Camera model. |
| `documentation` | string |  | Documentation filename, path or URL |
| `image_size` | array[<a href="#unit">Unit</a>] | ✅ | Size of the image length unit squared. |
| `field_of_view` | array[<a href="#unit">Unit</a>] |  | Size of the field of view in length unit squared. |
| `image_scale` | <a href="#unit">Unit</a> |  | Scale of the image in pixels per length unit. |
| `focal_length` | <a href="#unit">Unit</a> |  | Focal length of the lens in length unit. |
| `lens` | string |  | Lens manufacturer and model names. |
| `filter` | string |  | Filter type, manufacturer and model. |
| `aperture` | string |  | Aperture of the lens, example: f/8 |
| `exposure` | <a href="#unit">Unit</a> |  | Exposure time in time unit. |
| `standoff_distance` | <a href="#unit">Unit</a> |  | Distance between the camera and the sample. |
| `uncertainty` | <a href="#unit">Unit</a> |  | Estimation of image noise. |

### Infrared Camera (`data_sources/infrared`)

Generic infrared camera

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/infrared" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the infrared camera. |
| `description` | string |  | comments and additional informations |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of channels of the ouput data |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface'. |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer, Brand |
| `model` | string |  | Model |
| `documentation` | string |  | Documentation filename, path or URL |
| `image_size` | array[<a href="#unit">Unit</a>] | ✅ | Size of the image length unit squared. |
| `field_of_view` | array[<a href="#unit">Unit</a>] |  | Size of the field of view in length unit squared. |
| `image_scale` | <a href="#unit">Unit</a> |  | Scale of the image in pixels per length unit. |
| `focal_length` | <a href="#unit">Unit</a> |  | Focal length of the lens in lenght unit. |
| `lens` | string |  | Camera lens manufacturer and model names. |
| `filter` | string |  | Filter type, manufacturer and model. |
| `aperture` | string |  | Aperture of the lens. |
| `exposure` | <a href="#unit">Unit</a> |  | Exposure time in time unit. |
| `standoff_distance` | <a href="#unit">Unit</a> |  | Standoff distance between the camera and the sample in length unit. |
| `bandwidth` | array[<a href="#unit">Unit</a>] | ✅ | Bandwidth [item0, item1] |
| `emissivity` | <a href="#unit">Unit</a> |  | Emissivity |
| `transmissivity` | <a href="#unit">Unit</a> |  | Transmissivity |
| `nuc_file` | string |  | Non Uniformity Correction |
| `calibration_file` | string |  | filename |
| `uncertainty` | <a href="#unit">Unit</a> |  | estimation of image noise. |

### Tomograph X-Ray (`data_sources/tomograph`)

Generic tomograph

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/tomograph" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Title of the tomograph. |
| `description` | string |  | Description of the tomograph. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of channels of the ouput data. |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface' for radios or 'volume' for scans. |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer, vendor or software editor. |
| `model` | string |  | Model or software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `image_size` | array[<a href="#unit">Unit</a>] | ✅ | Size of the image pixels. |
| `field_of_view` | array[<a href="#unit">Unit</a>] |  | Size of the field of view in length unit. |
| `image_scale` | <a href="#unit">Unit</a> |  | Scale of the image in pixels per length unit. |
| `source` | string | ✅ | Source characteristics. |
| `voltage` | <a href="#unit">Unit</a> |  | Used voltage. |
| `current` | <a href="#unit">Unit</a> |  | electric current. |
| `detector` | string |  | electric current. |
| `scan_duration` | <a href="#unit">Unit</a> |  | Scan duration |
| `target` | string |  | reflexion target. |
| `tube_to_detector_distance` | <a href="#unit">Unit</a> |  | Distance between the tube and the detector. |
| `source_to_object_distance` | <a href="#unit">Unit</a> |  | Distance between the source and the object. |
| `number_of_projections` | unsigned integer |  | number of radiographs. |
| `angular_amplitude` | <a href="#unit">Unit</a> |  | amplitude in degree, example: 360 |
| `aquisition_param_file` | string |  | filename |
| `reconstruction_param_file` | string |  | filename |
| `uncertainty` | <a href="#unit">Unit</a> |  | estimation of image noise or artifacts. |

### Load Cell (`data_sources/load_cell`)

Load cell, Force cell

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/load_cell" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Load cell name |
| `description` | string |  | Description of the load cell |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components of the ouput data, example 1 for single axis or 6 for 6-axis sensors |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'point' |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer, vendor, brand. |
| `model` | string |  | Model. |
| `documentation` | string |  | Documentation filename, path or URL |
| `type` | string |  | (e.g. wheatstone, piezzo-electric, FSR). |
| `capacity` | <a href="#unit">Unit</a> | ✅ | Capacity of the load cell / Force range. |
| `uncertainty` | <a href="#unit">Unit</a> |  | Quantification of data uncertainty. |

### Strain Gauge (`data_sources/strain_gauge`)

Strain gauge, Rosette, Extensometer...

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/strain_gauge" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Strain gauge name |
| `description` | string |  | Description of the load cell |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components of the ouput data, example: 1 or 3 for rosette. |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'point' |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer, Vendor or brand. |
| `model` | string |  | Model. |
| `documentation` | string |  | Documentation filename, path or URL |
| `length` | <a href="#unit">Unit</a> | ✅ | Gauge or measuring length |
| `uncertainty` | <a href="#unit">Unit</a> |  | Uncertainty or resolution of strain. |

### Point Temperature (`data_sources/point_temperature`)

thermocouples, Resistance Temperature Detectors (RTDs), thermistor, pyrometer...

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/point_temperature" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Thermometer name |
| `description` | string |  | Description of thermometer |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components of the ouput data, should be 1 |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'point' |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | Unit of the output data. |
| `manufacturer` | string |  | Manufacturer, vendor or software editor. |
| `model` | string |  | Model or software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `range` | array[<a href="#unit">Unit</a>] | ✅ | Temperature range [item0, item1] |
| `emissivity` | <a href="#unit">Unit</a> |  | Pyrometer emissivity |
| `uncertainty` | <a href="#unit">Unit</a> |  | uncertainty or resolution. |

### Digital Image Correlation measurement (`data_sources/dic_measurement`)

DIC, DVC, Stereo DIC

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/dic_measurement" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Name of the DIC measurement. |
| `description` | string |  | Description of the DIC measurement. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface' for DIC or 'volume' for DVC |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | examples: pixels, voxels, length unit... |
| `manufacturer` | string |  | Software editor. |
| `model` | string |  | Software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `subset_size` | array[<a href="#unit">Unit</a>] |  | Size of the subset length unit squared. |
| `step_size` | <a href="#unit">Unit</a> |  | distance between two adjacent subsets |
| `mesh` | string |  | Finite Element or BSpline mesh: filename or specimen setting id |
| `image_filtering` | string |  | Type of filter and kernel |
| `interpolant` | string |  | Subpixel interpolation: linear, cubic spline |
| `matching_criterion` | string | ✅ | ZNSSD, ZNCC or other ... |
| `shape_function` | string |  | affine, quadratic, linear triangles TRI3 ... |
| `camera_model` | string |  | no, pinhole, distortions modes...  |
| `camera_parameters` | string |  | filename or list of parameters |
| `regularization_type` | string |  | strong/weak + type: gradient, elastic... |
| `regularisation_length` | <a href="#unit">Unit</a> |  | length or weight |
| `uncertainty` | <a href="#unit">Unit</a> |  | e.g. uncertainty on the output field |

### Mechanical analysis (`data_sources/mechanical_analysis`)

numerical simulation of a mechanical model

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/mechanical_analysis" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Name of the data analysis. |
| `description` | string |  | Description of the mechanical model. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface' for 2D or 'volume' for 3D |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | examples: %, microdefs... |
| `manufacturer` | string | ✅ | Software name. |
| `model` | string |  | Software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `parameters` | array[<a href="#unit">Unit</a>] |  | constitutive, geometric, loading or numerical parameters  |
| `uncertainty` | <a href="#unit">Unit</a> |  | estimation of numerical errors |

### Parameter identification (`data_sources/identification`)

inverse problem or model updating

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/identification" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Name of the inverse analysis. |
| `description` | string |  | Description of the identification method and parameters used. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface' for 2D or 'volume' for 3D |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | examples: %, microdefs... |
| `manufacturer` | string |  | Software name. |
| `model` | string |  | Software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `parameters` | array[<a href="#unit">Unit</a>] |  | constitutive, geometric, loading or numerical parameters  |
| `uncertainty` | <a href="#unit">Unit</a> |  | estimation of identification uncertainty |

### Computing strains from displacement field (`data_sources/strain_computation`)

Post-processing measured of simulated displacement fields to compute strains

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data source. |
| `kind` | "data_sources/strain_computation" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string |  | Name of the data analysis. |
| `description` | string |  | Additional description of the way strains are computed from displacements. |
| `input_data_sets` | array[Data set id] |  | Data sets IDs serving as an input to the source. |
| `output_components` | unsigned integer | ✅ | Number of components |
| `output_dimension` | "point" \| "curve" \| "surface" \| "volume" | ✅ | should be 'surface' for 2D or 'volume' for 3D |
| `output_units` | array[<a href="#unit">Unit</a>] | ✅ | examples: %, microdefs... |
| `manufacturer` | string |  | Software name. |
| `model` | string |  | Software version. |
| `documentation` | string |  | Documentation filename, path or URL |
| `virtual_strain_gauge_size` | <a href="#unit">Unit</a> | ✅ |   |
| `displacement_filtering` | string |  | Type of filter and kernel |
| `strain_filtering` | string |  | Type of filter and kernel |
| `uncertainty` | <a href="#unit">Unit</a> |  | estimation of uncertainty on the output |


## Data Sets

A data set gives the organisation of the measured or generated data and time resolution.

Allowed item kinds: Generic \| File \| List

### Generic data set (`data_sets/generic`)

Description of the data set.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data set. |
| `kind` | "data_sets/generic" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the data set. |
| `description` | string | ✅ | Description of the data set. |
| `file_type` | string | ✅ | MIME type of the file. |
| `path` | string | ✅ | Relative path to the data file. |
| `data_sources` | array[Data source id] | ✅ | List of IDs of the data sources. |

### Data set (single file) (`data_sets/file`)

When all the timestamps and data is stored in a single tablular like file (like csv or txt). If the timestamps and data are in two separate files they should be in the same folder.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data set. |
| `kind` | "data_sets/file" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the data set. |
| `description` | string | ✅ | Description of the data set. |
| `folder` | string |  | Relative path to the folder containing the timestamps and data file(s). |
| `data_sources` | array[Data source id] | ✅ | List of IDs of the data sources. |
| `time_reference` | number | ✅ | Time serving as a reference to the whole data set. |
| `keywords` | array[string] |  | List of keywords. |
| `timestamps` | <a href="#data-set-file">Data set file</a> | ✅ | Path and range to the timestamps file |
| `data` | <a href="#data-set-file">Data set file</a> | ✅ | Path and range to the data file |

### Data set (list of files) (`data_sets/list`)

When all the data is stored in separated files (like a list of images). They should all be in the same folder.

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | ID of the data set. |
| `kind` | "data_sets/list" (fixed) | ✅ | Only required for specs implementation purposes. |
| `title` | string | ✅ | Title of the data set. |
| `description` | string | ✅ | Description of the data set. |
| `path` | string |  | Relative path to the data folder. |
| `file_type` | string | ✅ | MIME type of the data files. |
| `data_sources` | array[Data source id] | ✅ | List if IDs of the data sources. |
| `time_reference` | <a href="#unit">Unit</a> | ✅ | Time serving as a reference to the whole data set. |
| `keywords` | array[string] |  | List of keywords. |
| `timestamps` | array[number] | ✅ | List of the timestamps. |
| `data` | array[string] | ✅ | List of the data files. |

## Appendix — Common Types

### Setting id

ID of a setting.

| Property | Value |
|---|---|
| `type` | string |

### Data set id

ID of a data set.

| Property | Value |
|---|---|
| `type` | string |

### Data source id

ID of a data source.

| Property | Value |
|---|---|
| `type` | string |

### Data set file

| Field | Type | Required | Description |
|---|---|---|---|
| `filename` | string | ✅ |  |
| `file_type` | string |  | MIME type of the file. |
| `delimiter` | string |  |  |
| `data_range` | string |  |  |
| `kind` | "data_set_file" (fixed) | ✅ | Only required for specs implementation purposes |

### Unit

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string |  | Title of the unit. |
| `value` | number |  | Numerical value. |
| `unit` | string | ✅ | Sign of the unit. |
| `scale` | number |  | Factor with respect to the standard system |
| `kind` | "unit" (fixed) | ✅ | Only required for specs implementation purposes |

### unsigned integer

Unsigned int

| Property | Value |
|---|---|
| `type` | integer |
