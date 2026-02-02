from r3xa_api import R3XAFile, data_set_file, schema_version, unit, validate


def ir_timestamps() -> list[float]:
    start = 10.0861051
    step = 0.008347218
    count = 263
    return [round(start + i * step, 7) for i in range(count)]


VISIBLE_TIMESTAMPS = [
    10.087318,
    10.122041,
    10.157072,
    10.192621,
    10.227715,
    10.263256,
    10.297692,
    10.331662,
    10.36756,
    10.400493,
    10.436335,
    10.469412,
    10.501326,
    10.535065,
    10.569657,
    10.605485,
    10.639419,
    10.674733,
    10.709984,
    10.743635,
    10.774395,
    10.80898,
    10.839176,
    10.87432,
    10.908327,
    10.944077,
    10.974152,
    11.007943,
    11.042306,
    11.078152,
    11.113481,
    11.148348,
    11.183672,
    11.218466,
    11.253091,
    11.288425,
    11.322835,
    11.358783,
    11.392888,
    11.423134,
    11.458234,
    11.493808,
    11.527986,
    11.563461,
    11.599103,
    11.633214,
    11.668772,
    11.70326,
    11.737971,
    11.773297,
    11.810441,
    11.845467,
    11.880118,
    11.915665,
    11.950018,
    11.985194,
    12.022466,
    12.057555,
    12.095647,
    12.131392,
    12.168176,
    12.203322,
    12.236564,
    12.271212,
]

CALIBRATION_SERIES = [
    (5, "000001", "03_51_56_079", 1, 99),
    (10, "000002", "03_55_44_255", 1, 99),
    (15, "000003", "04_21_55_591", 0, 99),
    (20, "000004", "04_25_05_416", 0, 99),
    (22, "000005", "04_27_20_850", 1, 99),
    (24, "000006", "04_31_26_142", 1, 99),
    (26, "000007", "04_32_52_342", 0, 99),
    (27, "000008", "04_34_08_043", 0, 99),
    (28, "000009", "04_35_14_043", 0, 99),
    (29, "000010", "04_36_14_759", 0, 99),
    (30, "000011", "04_37_45_993", 1, 99),
    (32, "000012", "04_39_03_910", 1, 99),
    (35, "000013", "04_41_25_102", 1, 99),
    (40, "000014", "04_42_55_185", 0, 99),
    (45, "000015", "04_44_30_844", 1, 99),
    (50, "000016", "04_45_39_411", 0, 99),
    (55, "000017", "04_47_39_352", 0, 99),
    (60, "000018", "04_49_20_419", 0, 99),
]

# Build file from scratch (no JSON input at runtime)
r3xa = R3XAFile(
    version=schema_version(),
    title="IR Lagrangian thermography - Qi Hu",
    description="Qi Hu experimental pipeline (IR + visible imaging, processing, DIC-like steps)",
    authors="J-F. Witz, Q. Hu",
    date="2024-10-30",
    repository="https://example.org/qi-hu",
    documentation="https://theses.hal.science/tel-04993338",
    license="GPL-2.0-or-later",
)

# Settings
r3xa.add_setting("settings/generic", id="sample", title="316L", description="316L")
r3xa.add_setting(
    "settings/generic",
    id="settings_Instron_tensile_test",
    title="Instron 8800",
    description="Electromechanical Machine",
)

# Data sources
camera_ir = r3xa.add_data_source(
    "data_sources/camera",
    id="camera_IR",
    title="FILR InfraRed Camera",
    description="FILR InfraRed Camera used for the test",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="gl", value=1.0, unit="gl", scale=1.0)],
    manufacturer="FLIR",
    model=" X6580sc",
    image_size=[
        unit(title="width", value=640, unit="px", scale=1.0),
        unit(title="height", value=512, unit="px", scale=1.0),
    ],
    image_scale=unit(title="image_scale", value=15, unit="µm/px", scale=1.0),
    lens="FLIR G1",
)

camera_visible = r3xa.add_data_source(
    "data_sources/camera",
    id="camera_visible",
    title="Ximea PCIe visible camera",
    description="Visible camera used ofr the test",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="gl", value=1.0, unit="gl", scale=1.0)],
    manufacturer="Ximea",
    model="CB500",
    image_size=[
        unit(title="width", value=5400, unit="px", scale=1.0),
        unit(title="height", value=4400, unit="px", scale=1.0),
    ],
    lens="LAOWA Utra-Macro 2.5-5x",
)

load_cell = r3xa.add_data_source(
    "data_sources/generic",
    id="load_cell",
    title="Load cell",
    description="Load cell of INSTRON 8800 300KN machine",
    output_components=1,
    output_dimension="point",
    output_units=[unit(title="N", value=1.0, unit="N", scale=1.0)],
    manufacturer="Instron",
    model="8800",
)

load_cell_visible_timeline = r3xa.add_data_source(
    "data_sources/generic",
    id="load_cell_visible_timeline",
    title="Load cell on visible timeline",
    description="Load cell interpolator on visible timeline",
    output_components=1,
    output_dimension="point",
    output_units=[unit(title="N", value=1.0, unit="N", scale=1.0)],
    manufacturer="Instron",
    model="8800",
    input_data_sets=["load_cell_data", "visible_images"],
)

calibration_ir = r3xa.add_data_source(
    "data_sources/generic",
    id="calibration_IR",
    title="Infra Red calibration process",
    description="Conversion from DL to T(°C)",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="°C", value=1.0, unit="°C", scale=1.0)],
    manufacturer="NUMPY",
    model="1.calibrited_ir_camera.py",
    input_data_sets=["IR_raws", "calibration_tables"],
)

dic = r3xa.add_data_source(
    "data_sources/generic",
    id="dic",
    title="DIC Analysis",
    description="Displacement measurement",
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="px", value=1.0, unit="px", scale=1.0)],
    manufacturer="YaDICs",
    model="v04.14a",
    input_data_sets=["visible_images"],
)

lagrangian_thermography = r3xa.add_data_source(
    "data_sources/generic",
    id="lagrangian_thermography",
    title="Lagrangian thermography",
    description=(
        "Lagrangian thermography computation from :\n"
        "    - rescaling IR images and following on visibe reference frame\n"
        "     - DIC field registration to be lagrangian"
    ),
    output_components=1,
    output_dimension="surface",
    output_units=[unit(title="°C", value=1.0, unit="°C", scale=1.0)],
    manufacturer="python/script",
    model="3.Langrangian thermography with Yadics.py",
    input_data_sets=["dic_fields", "temperature_fields_eulerian"],
)

energy_balance = r3xa.add_data_source(
    "data_sources/generic",
    id="energy_balance",
    title="Energy balance",
    description="Von Mises strains, Thermal flux, Taylor Quiney map computation",
    output_components=2,
    output_dimension="surface",
    output_units=[
        unit(title="°C", value=1.0, unit="°C", scale=1.0),
        unit(title="%", value=1.0, unit="%", scale=1.0),
    ],
    manufacturer="python/script",
    model="3.Langrangian thermography with Yadics.py",
    input_data_sets=[
        "dic_fields",
        "temperature_fields_lagrangian",
        "load_cell_data_interp_visible_timeline_data",
    ],
)

# Data sets
ir_files = [
    f"original images IR/Rec-1_serie_2450N-000001-001_02_06_49_467_{index}.tif"
    for index in range(2068, 2331)
]
ir_timeline = ir_timestamps()

r3xa.add_data_set(
    "data_sets/list",
    id="IR_raws",
    title="IR raws images",
    description="Raw images from the FLIR InfraRed Camera",
    path="original images IR/",
    file_type="image/tiff",
    data_sources=["camera_IR"],
    time_reference=0.0,
    timestamps=ir_timeline,
    data=ir_files,
)

calibration_files = []
for temp, seq, middle, start, end in CALIBRATION_SERIES:
    for index in range(start, end + 1):
        calibration_files.append(
            f"./calibration IR camera/{temp}/Rec-{temp}-{seq}-001_{middle}_{index}.tif"
        )

r3xa.add_data_set(
    "data_sets/list",
    id="calibration_tables",
    title="calibration tables",
    description="tables of Black body calibrations",
    path="./",
    file_type="image/tiff",
    data_sources=["camera_IR"],
    time_reference=0.0,
    timestamps=[],
    data=calibration_files,
)

r3xa.add_data_set(
    "data_sets/list",
    id="dic_fields",
    title="DIC fields",
    description="Visible DIC fields",
    path="./",
    file_type="application/x-netcdf",
    data_sources=["dic"],
    time_reference=0.0,
    timestamps=VISIBLE_TIMESTAMPS,
    data=["node.nc", "modes.nc"],
)

r3xa.add_data_set(
    "data_sets/file",
    id="load_cell_data",
    title="Load cell data",
    description="Load cell data",
    folder="./1_serie_2450N/",
    data_sources=["load_cell"],
    time_reference=0.0,
    timestamps=data_set_file(
        filename="1_serie_2450N/Traction_1.csv", delimiter=",", data_range="1:0:183799:1"
    ),
    data=data_set_file(filename="Traction_1.csv", delimiter=",", data_range="1:1:183799:1"),
)

visible_files = [
    f"original visible images/{index:06d}.tif" for index in range(294, 358)
]
visible_files.append("original visible images/ref.tif")

r3xa.add_data_set(
    "data_sets/list",
    id="visible_images",
    title="Visible images",
    description="visible images from Ximea camera",
    path="original visible images/",
    file_type="image/tiff",
    data_sources=["camera_visible"],
    time_reference=0.0,
    timestamps=VISIBLE_TIMESTAMPS,
    data=visible_files,
)

r3xa.add_data_set(
    "data_sets/list",
    id="load_cell_data_interp_visible_timeline_data",
    title="Load cell data interpolated on visible timeline data",
    description="load cell data interpolated on visible timeline data",
    path="./thermomechanical results/",
    file_type="application/octet-stream",
    data_sources=["load_cell_visible_timeline"],
    time_reference=0.0,
    timestamps=VISIBLE_TIMESTAMPS,
    data=["F_macro.npy"],
)

eulerian_files = [
    f"traction_temperature_field_ir_configuration/{index}.npy" for index in range(0, 263)
]

r3xa.add_data_set(
    "data_sets/list",
    id="temperature_fields_eulerian",
    title="Eulerian Temperature fields",
    description="Eulerian Temperature fields",
    path="./",
    file_type="application/octet-stream",
    data_sources=["calibration_IR"],
    time_reference=0.0,
    timestamps=[],
    data=eulerian_files,
)

lagrangian_files = [
    f"thermomechanical results/temperature_field_ccd_configuration_ROI/T_{index}.npy"
    for index in range(0, 64)
]

r3xa.add_data_set(
    "data_sets/list",
    id="temperature_fields_lagrangian",
    title="Lagrangian Temperature Field",
    description=(
        "Eulerian thermography registered\n"
        "after rescaling IR images and following on visibe reference frame\n"
        "and with the DIC field to be lagrangian"
    ),
    path="./",
    file_type="application/octet-stream",
    data_sources=["lagrangian_thermography"],
    time_reference=0.0,
    timestamps=VISIBLE_TIMESTAMPS,
    data=lagrangian_files,
)

energy_balance_files = [
    f"./traction_temperature_field_ir_configuration/{index}.npy" for index in range(0, 263)
]

r3xa.add_data_set(
    "data_sets/list",
    id="energy_balance_fields",
    title="Final results :\nLagrangian energy balance fields",
    description="Energy balance fields",
    path="./",
    file_type="application/octet-stream",
    data_sources=["energy_balance"],
    time_reference=0.0,
    timestamps=VISIBLE_TIMESTAMPS,
    data=energy_balance_files,
)

# Validate and save
payload = r3xa.to_dict()
validate(payload)
r3xa.save("examples/artifacts/qi_hu_from_scratch.json")
