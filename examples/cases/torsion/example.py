"""
## R3XA Example 0 - Real Torsion Experiment
Real example of a torsion test
"""
# %%
import r3xa_api as r3xa

"""
### 0. HEADER
Starting with authors
"""

pauline = r3xa.author(
    'P. Avetisyan',
    'Sorbonne Université',
    None
)

jeancharles = r3xa.author(
    'J. C. Passieux',
    'INSA-Toulouse - ICA',
    'https://orcid.org/0000-0001-8387-4122'
)

jeannoel  = r3xa.author(
    'J. N. Périé',
    'Toulouse University - ICA',
    'https://orcid.org/0000-0002-1522-3931'
)

"""
Construction of the R3XA `file` and filling the header info
"""

file = r3xa.R3XAFile(
   title="Large-Rotation Torsion Test on HMA Sample",
   description="Experimental dataset of torsion testing under large rotations (up to 400°) on a hot-melt adhesive (HMA) cylindrical " \
      "specimen including an a priori full 360° scan, used to benchmark mono-cam PhDIC",
   authors=[pauline, jeancharles, jeannoel],
   documentation = 'documentation.pdf',
   repository = 'https://doi.org/10.5281/zenodo.23420337',
   date="2025-07-02"
)

"""
### 1. SETTINGS
two spotlights + the testing machine + the sample + a calibration board
"""

lights = r3xa.new_generic_setting(
    title='Spotlights',
    description='2 Spotlights MultiLed QX 100% indirect\nGS Vitec SN : GS01224 and GS01225',
    documentation='https://www.blinktech.com.au/wp-content/uploads/2023/10/MULTILED_QX.pdf',
)

machine = r3xa.new_testing_machine_setting(
    title='Torsion apparatus',
    description='Andilog Twist torsion test stand, precision : 0,1 deg ',
    manufacturer = 'Andilog',
    model = 'Drivetwist',
    type = 'electromechanical', 
    capacity = r3xa.unit(value=40, unit='Nm')
)

sample = r3xa.new_specimen_setting(
    title='Sample',
    description = 'hot-melt adhesive (HMA) cylindrical specimen',
    patterning_technique = "matte black and white spray paint",
    sizes = [
        r3xa.unit(title='diameter', value=11.7, unit='mm'),
        r3xa.unit(title='length', value=150, unit='mm'),
    ]
)

calib_board = r3xa.new_generic_setting(
    title = 'calibration board',
    description = 'Circles grid of 12 x 9, spacing = 5 mm',
    grid = [12, 9],
    spacing = r3xa.unit(value=5, unit='mm')
)

"""
### 2. DATA SOURCES
"""

torque_sensor = r3xa.new_generic_source(
    title = 'Dynamic Torque sensor', 
    description = "Andilog Dynamic Torque sensor, capacity 6Nm, resolution 0.6mNm",
    output_components = 1,
    output_dimension = "point",
    output_units=[r3xa.unit(unit="Nm")],
    capacity = r3xa.unit(value=6, unit='Nm'),
    manufacturer = "Andilog",
    model = "SPIP TT 6",
    uncertainty = r3xa.unit(value=0.6, unit='mNm'),
    documentation = "https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html"
)

angle_sensor = r3xa.new_generic_source(
    title = 'Dynamic Angle sensor', 
    description = "Andilog Dynamic angle sensor",
    output_components = 1,
    output_dimension = "point",
    output_units=[r3xa.unit(unit="deg")],
    manufacturer = "Andilog",
    uncertainty = r3xa.unit(value=0.1, unit='deg'),
    documentation = "https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html"
)

camera = r3xa.new_camera_source(
    title="CCD Camera",
    output_components=1,
    output_dimension="surface",
    output_units=[r3xa.unit(unit="gl")],
    manufacturer="Flir",
    model="Grasshopper3 GS3-U3-51S5M",
    image_size=[
        r3xa.unit(title="width", value=2048, unit="px"),
        r3xa.unit(title="height", value=2048, unit="px"),
    ],
    image_scale = r3xa.unit(value=13.0, unit='px/m'),
    focal_length = r3xa.unit(value=50, unit='mm'),
    lens = 'Tamron C-Mount 50mm f/2.8',
    exposure = r3xa.unit(value=20.0, unit='ms'),
    standoff_distance = r3xa.unit(value=1.0, unit='m'),
    uncertainty = r3xa.unit(value=1.12, unit='gl')
)

"""
Linking the torque and angle sensors to the testing machine
"""

machine.attached_data_sources = [torque_sensor, angle_sensor]

"""
### 3. DATA SETS
Calibration grid images
"""

t0 = r3xa.unit(value=0.0, unit="s")

# Calibration images
image_files = ['img1-%2d.png' % i for i in range(72, 97)]
timestamps = [float(i) for i in range(72, 97)]

ds_calib_img = r3xa.new_list_data_set(
    title='Calibration images',
    description='grid image for intrinsic calibration',
    data_type='image/png',
    path="calib_img/",
    parent_data_sources=[camera,],
    time_reference=t0,
    timestamps=timestamps,
    values=image_files
    )

"""
Angles of the scanning phase
"""

times = r3xa.data_set_file(
    filename='resultats_angle&couple_rotation.csv',
    file_type="text/csv",
    delimiter=";",
    col = 'A',
    rows = [1, 63],
    )

angles = r3xa.data_set_file(
    filename='resultats_angle&couple_rotation.csv',
    file_type="text/csv",
    delimiter=";",
    col = 'C',
    rows = [1, 63],
    )

ds_rbm_angles = r3xa.new_file_data_set(
    title='Scanning Angles',
    description='Angles during the scan (rigid body rotation)',
    parent_data_sources=[angle_sensor],
    time_reference = t0,
    timestamps = times,
    values = angles
    )

"""
Images of the scanning phase
"""

image_files = ['img0-%02d.png' % i for i in range(0, 62)]
timestamps = [float(i) for i in range(0, 62)]

ds_scan_img = r3xa.new_list_data_set(
    title='Scanning images',
    description='Images taken during the scan (rigid body rotation)',
    data_type='image/png',
    path="rbm_img/",
    parent_data_sources=[camera,],
    time_reference=t0,
    timestamps=timestamps,
    values=image_files
    )

"""
Angles and Torques of the torsion experiment
"""

times2 = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="text/csv",
    delimiter=";",
    col = 'A',
    rows = [1, 73],
    )

angles2 = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="text/csv",
    delimiter=";",
    col = 'C',
    rows = [1, 73],
    )

torques = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="text/csv",
    delimiter=";",
    col = 'D',
    rows = [1, 73],
    )

ds_torsion_torques = r3xa.new_file_data_set(
    title='Torsion Torques',
    description='Torques during the Torsion test',
    parent_data_sources=[torque_sensor],
    time_reference = t0,
    timestamps = times2,
    values = torques
    )

ds_torsion_angles = r3xa.new_file_data_set(
    title='Torsion Angles',
    description='Angles during the Torsion test',
    parent_data_sources=[angle_sensor],
    time_reference = t0,
    timestamps = times2,
    values = angles2
    )

"""
Images of the torsion experiment
"""

image_files = ['img0-%02d.png' % i for i in range(0, 72)]
timestamps = [float(i) for i in range(0, 72)]

ds_torsion_img = r3xa.new_list_data_set(
    title='Torsion images',
    description='Images taken during the torsion test',
    data_type='image/png',
    path="torsion_img/",
    parent_data_sources=[camera,],
    time_reference=t0,
    timestamps=timestamps,
    values=image_files
    )

"""
### 4. CALIBRATION
"""

calib_engine = r3xa.new_generic_source(
    title='Camera Calibration',
    description='using Calibration_tool based on OpenCV',
    input_data_sets=[ds_calib_img],
    output_components=9, 
    output_dimension='point', 
    output_units=[
        r3xa.unit(title='center x', unit='px'),
        r3xa.unit(title='center y', unit='px'),
        r3xa.unit(title='focal x', unit='px'),
        r3xa.unit(title='focal y', unit='px'),
        r3xa.unit(title='k1', unit=''),
        r3xa.unit(title='k2', unit=''),
        r3xa.unit(title='k3', unit=''),
        r3xa.unit(title='p1', unit=''),
        r3xa.unit(title='p2', unit='')
        ],
    manufacturer='Calibration_tool based on OpenCV',
    model='v0.1'
    )

ds_intrinsics = r3xa.new_generic_data_set(
    title='Calibration parameters', 
    description='Intrisic parameters Cx, Cy, Fx, Fy and 5 distortion params', 
    parent_data_sources=[calib_engine], 
    file_type='text/txt',
    path='camera_intrinsics.txt'
    )


"""
Filling the File
"""

file.settings = [machine, sample, calib_board, lights]
file.data_sources = [torque_sensor, angle_sensor, camera, calib_engine]
file.data_sets = [ds_rbm_angles, ds_scan_img, ds_torsion_torques, ds_torsion_angles, ds_torsion_img, ds_calib_img, ds_intrinsics]

file.plot('outputs/example0_torsion')

print(file)

"""
Saving the File
"""

file.save('outputs/torsion_experiment.json')
