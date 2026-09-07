# %%
import r3xa_api as r3xa

print(r3xa.GenericSetting('',''))
print(r3xa.TestingMachineSettings('','',''))
print(r3xa.SpecimenSettings('','',''))
print(r3xa.StereorigSettings('','',''))

print(r3xa.GenericDataSource('','',1,'','','',''))
print(r3xa.CameraDataSource('',1,'','','',''))
print(r3xa.InfraredDataSource('',1,'','','',''))
print(r3xa.TomographDataSource('',1,'','','',''))
print(r3xa.LoadCellDataSource('',1,'','','',''))
print(r3xa.StrainGaugeDataSource('',1,'','','',''))
print(r3xa.PointTemperatureDataSource('',1,'','','',''))
print(r3xa.DicMeasurementDataSource('',1,'','','',''))
print(r3xa.MechanicalAnalysisDataSource('',1,'','','',''))
print(r3xa.IdentificationDataSource('',1,'','','',''))
print(r3xa.StrainComputationDataSource('',1,'','','',''))

print(r3xa.GenericDataSet('','','','',''))
print(r3xa.ListDataSet('','','','','','',''))
print(r3xa.FileDataSet('','','','','','',''))

# %%