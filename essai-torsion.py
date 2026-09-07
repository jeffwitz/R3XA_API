# -*- coding: utf-8 -*-
"""
Created on Mon Aug 31 12:35:24 2026

@author: passieux
"""
# %%
%matplotlib qt
import r3xa_api as r3xa

# my_file = r3xa.R3XAFile.load("save/essai-torsion-raw.json")

# %% Header
my_file = r3xa.R3XAFile(
    title="Torsion Test Pauline",
    description="Torsion test on a thermoplastic polymer stick",
    authors="P Avetisyan, JC Passieux and JN Périé",
    date="2025-07-02",
)

# %% Settings
machine = r3xa.new_setting.TestingMachineSettings(
    title="Torsion apparatus",
    description="Andilog Twist torsion test stand, precision : 0,1 deg",
    type = 'electromechanical device'
    )
machine.validate()
print(machine)


specimen = r3xa.new_setting.SpecimenSettings(
    title="Glue stick",
    description="Hot-melt adhesive cylinder stick",
    sizes=[r3xa.unit('diameter', 7, 'mm'), r3xa.unit('length', 150, 'mm')],
    patterning_technique="matte black and white spray paint",
    )
print(specimen)

board = r3xa.new_setting.GenericSetting(
    title='Calibration board',
    description='Vic circles calibration grid, 12x9, 5mm spacing',
    documentation='grid.svg'
    )
print(board)

lights = r3xa.new_setting.GenericSetting(
    title='Spot light',
    description='2 Spotlights MultiLed QX 100% indirect\nGS Vitec SN : GS01224\
    and GS01225',
    documentation='https://www.blinktech.com.au/wp-content/uploads/2023/10/MULTILED_QX.pdf'    
    )
print(lights)

my_file.settings = [machine, specimen, board, lights]
my_file.validate()
my_file.plot()

# %% Data Sources
torque_sensor = r3xa.new_datasource.GenericDataSource(
    title='Dynamic Torque sensor',
    description='Andilog Dynamic Torque sensor. \nCapacity 6Nm. \nResolution : 0,6 mNm',
    output_components=1,
    output_dimension='point',
    output_units=[r3xa.unit('torque', 0, 'N.m'),],
    manufacturer='Andilog',
    model='SPIP TT 6',
    documentation='https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html'
    )
print(torque_sensor)

angle_sensor = r3xa.new_datasource.GenericDataSource(
    title='Dynamic Angle sensor',
    description='Andilog Sensor embedded in the Torsion apparatus',
    output_components=1,
    output_dimension='point',
    output_units=[r3xa.unit('angle', 0, 'deg'),],
    manufacturer='Andilog',
    model='Twist Torsion test',
    documentation='https://pdf.directindustry.com/pdf/andilog-technologies/andilog-force-torque-measurements/7999-34677.html'
    )
print(angle_sensor)

camera = r3xa.new_datasource.CameraDataSource(
    title='Graylevel Camera',
    description='',
    output_components=1,
    output_dimension='surface',
    output_units=[r3xa.unit('graylevel', 0, 'gl'),],
    manufacturer="Flir",
    model="Grasshopper3 GS3-U3-51S5M",
    documentation="https://www.es-france.com/index.php?controller=attachment&id_attachment=14071",
    image_size=[r3xa.unit('row', 2048, 'px'), r3xa.unit('col', 2048, 'px')],
    image_scale=r3xa.unit('mm2px', 13.0, 'px/mm'),
    focal_length=r3xa.unit('f', 50, 'mm'),
    lens='Tamron C-Mount 50mm f/2.8',
    exposure=r3xa.unit('exp', 20, 'ms'),
    standoff_distance=r3xa.unit('sod', 1, 'm'),
    uncertainty=r3xa.unit('std', 1.12, 'gl')
    )
print(camera)

my_file.data_sources = [torque_sensor, angle_sensor, camera]

# %% Data sets
t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)

# Calibration images
image_files = ['calib_img/img1-%2d.png' % i for i in range(72, 97)]
timestamps = [float(i) for i in range(72, 97)]

data_calib_img = r3xa.new_dataset.ListDataSet(
    title='Calibration images',
    description='',
    file_type='image/png',
    data_sources=[camera.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=image_files
    )
print(data_calib_img)

my_file.data_sets += [data_calib_img, ]

# First rigid body rotation

times = r3xa.data_set_file(
    filename='resultats_angle&couple_rotation.csv',
    file_type="csv",
    delimiter=":",
    data_range="A2:A63",
    kind="data_set_file"
    )

angles = r3xa.data_set_file(
    filename='resultats_angle&couple_rotation.csv',
    file_type="csv",
    delimiter=":",
    data_range="C2:C63",
    kind="data_set_file"
    )

torques = r3xa.data_set_file(
    filename='resultats_angle&couple_rotation.csv',
    file_type="csv",
    delimiter=":",
    data_range="D2;D63",
    kind="data_set_file"
    )

data_rbm_torque = r3xa.new_dataset.FileDataSet(
    title='Torque RBM rotation',
    description='Torque during the rigid body rotation',
    data_sources=[torque_sensor.id],
    time_reference=t0,
    timestamps=times,
    data=torques
    )
data_rbm_torque.validate()

data_rbm_angle = r3xa.new_dataset.FileDataSet(
    title='Angle RBM rotation',
    description='Angles during the rigid body rotation',
    data_sources=[angle_sensor.id],
    time_reference=t0,
    timestamps=times,
    data=angles
    )

image_files = ['rbm_img/img0-%02d.png' % i for i in range(0, 62)]
timestamps = [float(i) for i in range(0, 62)]

data_rbm_img = r3xa.new_dataset.ListDataSet(
    title='Graylevel images RBM',
    description='',
    file_type='image/png',
    data_sources=[camera.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=image_files
    )

my_file.data_sets += [data_rbm_angle, data_rbm_torque, data_rbm_img]
my_file.validate()

# Torsion test

times2 = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="csv",
    delimiter=":",
    data_range="A2:A73",
    kind="data_set_file"
    )

angles2 = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="csv",
    delimiter=":",
    data_range="C2:C73",
    kind="data_set_file"
    )

torques2 = r3xa.data_set_file(
    filename='resultats_angle&couple_torsion.csv',
    file_type="csv",
    delimiter=":",
    data_range="D2;D73",
    kind="data_set_file"
    )

data_test_torque = r3xa.new_dataset.FileDataSet(
    title='Torque Torsion test',
    description='Torque during the torsion test',
    data_sources=[torque_sensor.id],
    time_reference=t0,
    timestamps=times2,
    data=torques2
    )

data_test_angle = r3xa.new_dataset.FileDataSet(
    title='Angle Torsion test',
    description='Angles during the torsion test',
    data_sources=[angle_sensor.id],
    time_reference=t0,
    timestamps=times2,
    data=angles2
    )

image_files = ['torsion_img/img0-%02d.png' % i for i in range(0, 72)]
timestamps = [float(i) for i in range(0, 72)]

data_test_img = r3xa.new_dataset.ListDataSet(
    title='Graylevel images Torsion',
    description='',
    file_type='image/png',
    data_sources=[camera.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=image_files
    )

my_file.data_sets += [data_test_angle, data_test_torque, data_test_img]

my_file.save('save/essai-torsion-raw.json')
my_file.plot()

# %% Calibration
calib_engine = r3xa.new_datasource.GenericDataSource(
    title='Camera Calibration',
    description='using Calibration_tool based on OpenCV',
    input_data_sets=[board.id, data_calib_img.id],
    output_components=9, 
    output_dimension='point', 
    output_units=[r3xa.unit('', 0, ''),],
    manufacturer='Calibration_tool based on OpenCV',
    model='v0.1'
    )

data_calib = r3xa.new_dataset.GenericDataSet(
    title='Calibration parameters', 
    description='Intrisic parameters f1, f2, c1, c2, and distortion', 
    data_sources=[calib_engine.id], 
    file_type='application/zip',
    path='intrisic_param.npz'
    )

data_calib.validate()

my_file.data_sources += [calib_engine, ]
my_file.data_sets += [data_calib]

#%% DIC

dic_engine = r3xa.new_datasource.DicMeasurementDataSource(
    title='2D DIC',
    description='inplace DIC',
    input_data_sets=[data_calib.id, data_test_img.id, specimen.id],
    output_components=2, 
    output_dimension='surface', 
    output_units=[r3xa.unit('displ', 0, 'mm'),], 
    matching_criterion='ZNSSD',
    manufacturer='pyxel',
    model='v2026',
    documentation='https://github.com/jcpassieux/pyxel',
    mesh='see specimen cad',
    image_filtering='no',
    interpolant='spline cubic',
    shape_function='linear triangles',
    camera_model='pinhole with distorsions',
    camera_parameters='see calib file',
    regularization_type='Tikhnonov',
    regularisation_length=r3xa.unit('', 10, 'mm'),
    uncertainty=r3xa.unit('', 0.2, 'mm')
    )

vtu_files = ['vtk/displ-%02d.png' % i for i in range(0, 72)]
timestamps = [float(i) for i in range(0, 72)]

data_dic = r3xa.new_dataset.ListDataSet(
    title='DIC Displacement',
    description='measured displacement',
    data_sources=[dic_engine.id],
    time_reference=t0,
    file_type='application/vnd.vtk',
    timestamps=timestamps,
    data=vtu_files
    )

my_file.data_sources += [dic_engine, ]
my_file.data_sets += [data_dic, ]

my_file.validate()
my_file.plot()

my_file.save('save/essai-torsion.json')


# %%
