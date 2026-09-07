
# %%
%matplotlib qt
import r3xa_api as r3xa

my_file = r3xa.R3XAFile(
    title="R3XA tutorial 3",
    description="example of a stereo rig",
    authors="JC Passieux",
    date="2026-09-02",
)

cam0 = r3xa.new_datasource.CameraDataSource(
    title='Camera 0',
    description='',
    output_components=1,
    output_dimension='surface',
    output_units=[r3xa.unit('graylevel', 0, 'gl'),],
    manufacturer="Flir",
    model="Grasshopper3 GS3-U3-51S5M",
    image_size=[r3xa.unit('row', 2048, 'px'), r3xa.unit('col', 2048, 'px')]
    )

cam1 = r3xa.new_datasource.CameraDataSource(
    title='Camera 1',
    description='',
    output_components=1,
    output_dimension='surface',
    output_units=[r3xa.unit('graylevel', 0, 'gl'),],
    manufacturer="Flir",
    model="Grasshopper3 GS3-U3-51S5M",
    image_size=[r3xa.unit('row', 2048, 'px'), r3xa.unit('col', 2048, 'px')]
    )

rig = r3xa.new_setting.StereorigSettings(
    title='StereoRig',
    description='',
    stereo_angle=r3xa.unit(title='angle', value=20.2, unit='°', scale=1),
    associated_data_sources=[cam0.id, cam1.id]
    )
rig.validate()

my_file.data_sources += [cam0, cam1]

board = r3xa.new_setting.Settings(
    title='Calibration board',
    description='Circles grid, 12x9, 5mm spacing'
    )
my_file.settings += [board, rig,]

imcalib0 = ['calib0-%2d.png' % i for i in range(30)]
imcalib1 = ['calib1-%2d.png' % i for i in range(30)]
t0 = r3xa.unit(title="time_reference", value=0.0, unit="s", scale=1.0)
timestamps = [float(i) for i in range(30)]

calib0 = r3xa.new_dataset.ListDataset(
    title='left calib img',
    description='',
    file_type='image/png',
    data_sources=[cam0.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=imcalib0
    )

calib1 = r3xa.new_dataset.ListDataset(
    title='right calib img',
    description='',
    file_type='image/png',
    data_sources=[cam1.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=imcalib1
    )

my_file.data_sets += [calib0, calib1]

calibration = r3xa.new_datasource.DataSource(
    title='Calibration Tool',
    description='',
    input_data_sets=[board.id, calib0.id, calib1.id],
    output_components=9, 
    output_dimension='point', 
    output_units=[r3xa.unit('', 0, ''),]
    )

calib_res = r3xa.new_dataset.Dataset(
    title='Calibration parameters', 
    description='Intrisic parameters f1, f2, c1, c2, and distortion', 
    data_sources=[calibration.id], 
    file_type='application/zip',
    path='intrisic_param.npz'
    )

my_file.data_sources += [calibration, ]
my_file.data_sets += [calib_res]

im0 = ['img0-%2d.png' % i for i in range(72, 97)]
im1 = ['img1-%2d.png' % i for i in range(72, 97)]
timestamps = [float(i) for i in range(72, 97)]

img0 = r3xa.new_dataset.ListDataset(
    title='left images',
    description='',
    file_type='image/png',
    data_sources=[cam0.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=im0
    )

img1 = r3xa.new_dataset.ListDataset(
    title='right images',
    description='',
    file_type='image/png',
    data_sources=[cam1.id, ],
    time_reference=t0,
    timestamps=timestamps,
    data=im1
    )

my_file.data_sets += [img0, img1]

dic = r3xa.new_datasource.DicMeasurementDataSource(
    title='Stereo DIC',
    description='',
    input_data_sets=[img0.id, img1.id, calib_res.id, ],
    output_components=3, 
    output_dimension='surface', 
    output_units=[r3xa.unit('displ', 0, 'mm'),], 
    matching_criterion='ZNSSD'
    )

my_file.data_sources += [dic,]

vtu_files = ['vtk/displ-%02d.png' % i for i in range(72, 97)]

displ = r3xa.new_dataset.ListDataset(
    title='DIC Displacement',
    description='',
    data_sources=[dic.id],
    time_reference=t0,
    file_type='application/vnd.vtk',
    timestamps=timestamps,
    data=vtu_files
    )

my_file.data_sets += [displ,]

my_file.plot()



# %%
