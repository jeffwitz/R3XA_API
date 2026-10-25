import marimo

__generated_with = "0.20.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    from pathlib import Path

    artifacts = Path(__file__).resolve().parents[4] / "artifacts" / "examples"
    return artifacts, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## R3XA Example 0 - Real Torsion Experiment
    Real example of a torsion test
    """)
    return


@app.cell
def _():
    import r3xa_api as r3xa

    return (r3xa,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 0. HEADER
    Starting with authors
    """)
    return


@app.cell
def _(r3xa):
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
    return jeancharles, jeannoel, pauline


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Construction of the R3XA `file` and filling the header info
    """)
    return


@app.cell
def _(jeancharles, jeannoel, pauline, r3xa):
    file = r3xa.R3XAFile(
       title="Large-Rotation Torsion Test on HMA Sample",
       description="Experimental dataset of torsion testing under large rotations (up to 350°) on a hot-melt adhesive (HMA) cylindrical " \
          "specimen including an a priori full 360° scan, used to benchmark mono-cam PhDIC",
       authors=[pauline, jeancharles, jeannoel],
       repository="https://doi.org/10.5281/zenodo.23420337",
       date="2025-07-02"
    )
    return (file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1. SETTINGS
    two spotlights + the testing machine + the sample + a calibration board
    """)
    return


@app.cell
def _(r3xa):
    lights = r3xa.new_generic_setting(
        id="stg-generic-torsion-lights",
        title='Spotlights',
        description='2 Spotlights MultiLed QX 100% indirect\nGS Vitec SN : GS01224 and GS01225',
        documentation='https://www.blinktech.com.au/wp-content/uploads/2023/10/MULTILED_QX.pdf',
    )

    machine = r3xa.new_testing_machine_setting(
        id="stg-testing-machine-torsion-apparatus",
        title='Torsion apparatus',
        description='Andilog Twist torsion test stand, precision : 0,1 deg ',
        manufacturer = 'Andilog',
        model = 'Drivetwist',
        type = 'electromechanical', 
        capacity = r3xa.unit(value=40, unit='Nm')
    )

    sample = r3xa.new_specimen_setting(
        id="stg-specimen-torsion-sample",
        title='Sample',
        description = 'hot-melt adhesive (HMA) cylindrical specimen',
        patterning_technique = "matte black and white spray paint",
        sizes = [
            r3xa.unit(title='diameter', value=7, unit='mm'),
            r3xa.unit(title='length', value=150, unit='mm'),
        ]
    )

    calib_board = r3xa.new_generic_setting(
        id="stg-generic-torsion-calibration-board",
        title = 'calibration board',
        description = 'Circles grid of 12 x 9, spacing = 5 mm',
        grid = [12, 9],
        spacing = r3xa.unit(value=5, unit='mm')
    )
    return calib_board, lights, machine, sample


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2. DATA SOURCES
    """)
    return


@app.cell
def _(r3xa):
    torque_sensor = r3xa.new_generic_source(
        id="src-generic-torsion-torque-sensor",
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
        id="src-generic-torsion-angle-sensor",
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
        id="src-camera-torsion-camera",
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
    return angle_sensor, camera, torque_sensor


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Linking the torque and angle sensors to the testing machine
    """)
    return


@app.cell
def _(angle_sensor, machine, torque_sensor):
    machine.attached_data_sources = [torque_sensor, angle_sensor]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 3. DATA SETS
    Calibration grid images
    """)
    return


@app.cell
def _(camera, r3xa):
    t0 = r3xa.unit(value=0.0, unit='s')
    _image_files = ['img1-%2d.png' % i for i in range(72, 97)]
    # Calibration images
    _timestamps = [float(i) for i in range(72, 97)]
    ds_calib_img = r3xa.new_list_data_set(id="set-list-torsion-calibration-images", title='Calibration images', description='grid image for intrinsic calibration', data_type='image/png', path='calib_img/', parent_data_sources=[camera], time_reference=t0, timestamps=_timestamps, values=_image_files)
    return ds_calib_img, t0


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Angles of the scanning phase
    """)
    return


@app.cell
def _(angle_sensor, r3xa, t0):
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
        id="set-file-torsion-scan-angles",
        title='Scanning Angles',
        description='Angles during the scan (rigid body rotation)',
        parent_data_sources=[angle_sensor],
        time_reference = t0,
        timestamps = times,
        values = angles
        )
    return (ds_rbm_angles,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Images of the scanning phase
    """)
    return


@app.cell
def _(camera, r3xa, t0):
    _image_files = ['img0-%02d.png' % i for i in range(0, 62)]
    _timestamps = [float(i) for i in range(0, 62)]
    ds_scan_img = r3xa.new_list_data_set(id="set-list-torsion-scanning-images", title='Scanning images', description='Images taken during the scan (rigid body rotation)', data_type='image/png', path='rbm_img/', parent_data_sources=[camera], time_reference=t0, timestamps=_timestamps, values=_image_files)
    return (ds_scan_img,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Angles and Torques of the torsion experiment
    """)
    return


@app.cell
def _(angle_sensor, r3xa, t0, torque_sensor):
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
        id="set-file-torsion-torque-series",
        title='Torsion Torques',
        description='Torques during the Torsion test',
        parent_data_sources=[torque_sensor],
        time_reference = t0,
        timestamps = times2,
        values = torques
        )

    ds_torsion_angles = r3xa.new_file_data_set(
        id="set-file-torsion-angle-series",
        title='Torsion Angles',
        description='Angles during the Torsion test',
        parent_data_sources=[angle_sensor],
        time_reference = t0,
        timestamps = times2,
        values = angles2
        )
    return ds_torsion_angles, ds_torsion_torques


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Images of the torsion experiment
    """)
    return


@app.cell
def _(camera, r3xa, t0):
    _image_files = ['img0-%02d.png' % i for i in range(0, 72)]
    _timestamps = [float(i) for i in range(0, 72)]
    ds_torsion_img = r3xa.new_list_data_set(id="set-list-torsion-images", title='Torsion images', description='Images taken during the torsion test', data_type='image/png', path='torsion_img/', parent_data_sources=[camera], time_reference=t0, timestamps=_timestamps, values=_image_files)
    return (ds_torsion_img,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 4. CALIBRATION
    """)
    return


@app.cell
def _(ds_calib_img, r3xa):
    calib_engine = r3xa.new_generic_source(
        id="src-generic-torsion-camera-calibration",
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
        id="set-generic-torsion-camera-intrinsics",
        title='Calibration parameters', 
        description='Intrisic parameters Cx, Cy, Fx, Fy and 5 distortion params', 
        parent_data_sources=[calib_engine], 
        file_type='text/txt',
        path='camera_intrinsics.txt'
        )
    return calib_engine, ds_intrinsics


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Filling the File
    """)
    return


@app.cell
def _(
    angle_sensor,
    calib_board,
    calib_engine,
    camera,
    ds_calib_img,
    ds_intrinsics,
    ds_rbm_angles,
    ds_scan_img,
    ds_torsion_angles,
    ds_torsion_img,
    ds_torsion_torques,
    file,
    lights,
    machine,
    sample,
    torque_sensor,
):
    file.settings = [machine, sample, calib_board, lights]
    file.data_sources = [torque_sensor, angle_sensor, camera, calib_engine]
    file.data_sets = [ds_rbm_angles, ds_scan_img, ds_torsion_torques, ds_torsion_angles, ds_torsion_img, ds_calib_img, ds_intrinsics]
    return


@app.cell
def _(artifacts, file, mo):
    file.validate()
    file.save(artifacts / 'torsion_experiment.json')
    svg_path = file.plot(artifacts / 'graph_torsion_experiment.svg')
    mo.Html(
        '<div class="r3xa-inline-graph">'
        + svg_path.read_text(encoding='utf-8')
        + '</div>'
    )
    return


@app.cell
def _(file):
    print(file)
    return


if __name__ == "__main__":
    app.run()
