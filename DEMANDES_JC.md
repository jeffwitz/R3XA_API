# GT Logiciels et Données Ouvertes
### R3XA - Remember, Reuse and Replicate eXperiments and Analyses
![](https://r3xa-api.readthedocs.io/en/latest/_images/R3XA.png =300x)

--- 
### Point 7/9/26

TODO:
- [ ] modifier le forçage du .env [name=Jeff]
- [ ] modifier le schema [name=JC]
    - [x] homogeneiser les required (id, kind et title)
    - [ ] listdataset.data > list_of_files > values ?
    - [x] path et data
    - [x] filedataset.folder > path   et  data reste data.
    - [x] file_type > mime_type
- [x] faire une branche de l'API ? [name=JC]
- [ ] écrire petit texte + répondre mail JAN [name=JC]
- [ ] webGUI: check sessions parallèles
    - [ ] demander à Julien pour un serveur python. installer des serveurs python sur la machine qui nous héberge.
    - [ ] sinon lancer un projet full JavaScript.
- [x] envoyer un email 30 sept [name=JC]
- [ ] regarder Model Contexte Provider (MCP) sur gitlab [name=Manu]

prochaine **réunion le mercredi 30 à 09:00**
https://visio.numerique.gouv.fr/ndb-bwrv-fvb

---
### Réunion 31 aout 2026
**1. Point sur les derniers avancements:**
- Développement de 3 dépots (R3XA_SPEC, R3XA_API et R3XA_REGISTRY) [name=Jeff]
- Développement d'une interface notebook web [name=Jeff]
- Evolutions du **Schema JSON**:
    - [ ] format de la **date** ? actuellement string ?
    - [ ] rajouter un flag **données brutes /données d'analyse** ?
    - [ ] LSA avec fullfieldmeasurement or NOT?
    - [ ] un maillage de l'éprouvette, c'est dans Setting Specimen ou dans GenericDataSet.
    - [ ] Est-ce qu'on peut avoir un GenericDataSet sans source ?
    - [x] manque le file_type dans "data_set" de type "file"
    - [x] file_type > mime_type
    - [x] corriger le **dataset_file**, c'est pas clair
    - [x] un truc pas clair entre path et data en fonction du data_set type
    - [x] homogeneisation des **required**, actuellement n'importe quoi. Proposition: Required uniquement pour id, kind et title.
    - [ ] **anyOf** plutôt que **oneOf** pour les unions discriminées
    ```
    Vos trois tableaux (settings, data_sources, data_sets) utilisent anyOf avec un discriminant kind en const. Ça fonctionne (grâce à additionalProperties: false, un objet ne peut valider qu'une seule branche), mais oneOf serait plus correct sémantiquement et donne de bien meilleurs messages d'erreur dans la plupart des validateurs (Ajv, par exemple, indique clairement quelle branche a échoué et pourquoi avec oneOf, alors qu'avec anyOf il additionne souvent toutes les erreurs de toutes les branches).
    ```
    - [ ] `data_sources` à l'intérieur de `data_sets/*`
    ```
    remplacer par produced_by ou generated_by
    inversement associated_data_source > equipped_with
    ```
    - [ ] `setting_id`, `data_set_id`, `data_source_id` sont tous de simples string sans pattern.
    ```
    Rien n'empêche une collision de nommage entre un ID de setting et un ID de data_source (les espaces de noms sont plats). Pour un schéma dont l'objectif est justement la traçabilité et la réplicabilité, je suggérerais soit un pattern (ex: préfixe stg-, src-, set-), soit au minimum des exemples dans le schéma qui illustrent la convention attendue, pour éviter que chaque labo invente la sienne et casse l'interopérabilité inter-datasets que R3XA est censé permettre.
    ```
    - [ ] `data_range` avec notation tableur pour du CSV > `col=2, rows=42-421`
    - [ ] Champ `authors` trop plat
    ```
    propose un tableau d'objets {nom, affiliation, orcid}
    ```

- Attribut **settings**
```
GenericSettings
───────────────────────────────────────────
id*                     : gdjmbygpgdslqdlqyiinojbq
kind*                   : settings/generic
title*                  : 
description*            : 
documentation           : None
associated_data_sources : None

TestingMachineSettings
───────────────────────────────────────────
id*                     : mfpjhylyhhqncjoxqefzerfo
kind*                   : settings/testing_machine
title*                  : 
description*            : 
type*                   : 
manufacturer            : None
model                   : None
documentation           : None
capacity                : None
associated_data_sources : None

SpecimenSettings
───────────────────────────────────────────
id*                     : aztszrbizousbseiqgtpzxbe
kind*                   : settings/specimen
title*                  :
description*            :
cad                     : None
sizes*                  :
patterning_technique    : None
patterning_feature_size : None

StereorigSettings
───────────────────────────────────────────
id*                     : lojdatsnlxsuowkxgjagncid
kind*                   : settings/stereorig
title*                  :
description*            :
stereo_angle*           :
calibration_target_type : None
calibration_target_size : None
associated_data_sources : None
```
- Attribut **data_sources**
```
GenericDataSource
──────────────────────────────────────
id*                : schkjhcejudnulggakxzwtzr
kind*              : data_sources/generic
title*             :
description*       :
input_data_sets    : None
output_components* : 1
output_dimension*  :
output_units*      :
manufacturer*      :
model*             :
documentation      : None
uncertainty        : None

CameraDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/camera
title*             :
description        : None
input_data_sets    : None
output_components* : 1
output_dimension*  :
output_units*      :
manufacturer       : None
model              : None
documentation      : None
image_size*        :
field_of_view      : None
image_scale        : None
focal_length       : None
lens               : None
filter             : None
aperture           : None
exposure           : None
standoff_distance  : None
uncertainty        : None

InfraredDataSource
──────────────────────────────────────
id*                : lppdpsacdshaogiotclxazej
kind*              : data_sources/infrared
title*             :
description        : None
input_data_sets    : None
output_components* : 1
output_dimension*  :
output_units*      :
manufacturer       : None
model              : None
documentation      : None
image_size*        :
field_of_view      : None
image_scale        : None
focal_length       : None
lens               : None
filter             : None
aperture           : None
exposure           : None
standoff_distance  : None
bandwidth*         :
emissivity         : None
transmissivity     : None
nuc_file           : None
calibration_file   : None
uncertainty        : None

TomographDataSource
─────────────────────────────────────────────
id*                       :
kind*                     : data_sources/tomograph
title                     : None
description               : None
input_data_sets           : None
output_components*        :
output_dimension*         : 1
output_units*             :
manufacturer              : None
model                     : None
documentation             : None
image_size*               :
field_of_view             : None
image_scale               : None
source*                   :
voltage                   : None
current                   : None
detector                  : None
scan_duration             : None
target                    : None
tube_to_detector_distance : None
source_to_object_distance : None
number_of_projections     : None
angular_amplitude         : None
aquisition_param_file     : None
reconstruction_param_file : None
uncertainty               : None

LoadCellDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/load_cell
title              :
description        : None
input_data_sets    : None
output_components* :
output_dimension*  : 1
output_units*      :
manufacturer       : None
model              : None
documentation      : None
type               : None
capacity*          :
uncertainty        : None

StrainGaugeDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/strain_gauge
title              :
description        : None
input_data_sets    : None
output_components* :
output_dimension*  : 1
output_units*      :
manufacturer       : None
model              : None
documentation      : None
length*            :
uncertainty        : None

PointTemperatureDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/point_temperature
title              :
description        : None
input_data_sets    : None
output_components* :
output_dimension*  : 1
output_units*      :
manufacturer       : None
model              : None
documentation      : None
range*             :
emissivity         : None
uncertainty        : None

DicMeasurementDataSource
─────────────────────────────────────────
id*                   :
kind*                 : data_sources/dic_measurement
title                 :
description           : None
input_data_sets       : None
output_components*    :
output_dimension*     : 1
output_units*         :
manufacturer          : None
model                 : None
documentation         : None
subset_size           : None
step_size             : None
mesh                  : None
image_filtering       : None
interpolant           : None
matching_criterion*   :
shape_function        : None
camera_model          : None
camera_parameters     : None
regularization_type   : None
regularisation_length : None
uncertainty           : None

MechanicalAnalysisDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/mechanical_analysis
title              :
description        : None
input_data_sets    : None
output_components* :
output_dimension*  : 1
output_units*      :
manufacturer*      :
model              : None
documentation      : None
parameters         : None
uncertainty        : None

IdentificationDataSource
──────────────────────────────────────
id*                :
kind*              : data_sources/identification
title              :
description        :
input_data_sets    : None
output_components* :
output_dimension*  : 1
output_units*      :
manufacturer       : None
model              : None
documentation      : None
parameters         : None
uncertainty        : None

StrainComputationDataSource
──────────────────────────────────────────────
id*                        :
kind*                      : data_sources/strain_computation
title                      :
description                : None
input_data_sets            : None
output_components*         :
output_dimension*          : 1
output_units*              :
manufacturer               : None
model                      : None
documentation              : None
virtual_strain_gauge_size* :
displacement_filtering     : None
strain_filtering           : None
uncertainty                : None
```
- Attribut **data_sets**
```
GenericDataSet
─────────────────────────────────
id*           : xdetkodziytgghayjzhiveol
kind*         : data_sets/generic
title*        :
description*  :
file_type*    :
path*         :
data_sources* :

ListDataSet
───────────────────────────────────
id*             : givufdnyfhcmbmjonvzeyexe
kind*           : data_sets/list
title*          :
description*    :
path            : None
file_type*      :
data_sources*   :
time_reference* :
keywords        : None
timestamps*     :
data*           :

FileDataSet
───────────────────────────────────
id*             :
kind*           : data_sets/file
title*          :
description*    :
folder          : None
data_sources*   :
time_reference* :
keywords        : None
timestamps*     :
data*           :
```

- Beta-test de **R3XA_API** > évolutions: [name=JC]
    - [ ] simplifier l'installation avec un dépot PyPI `pip install r3xa` > CI Gitlab [name=Manu]
    - [x] corriger le timereference de dataset_file (string)
    - [ ] faire une classe pour les settings, data_sources, data_sets pour pouvoir les valider, printer, les save et les load indépendamment du fichier R3XA.
    - [ ] ajouter une méthode pour lister les attributs optionnels pour aider l'utilisateur à renseigner les champs et ne pas en oublier.
:::success
Création de codegen_settings.py codegen_datasources.py, codegen_datasets.py qui intègrent les fonctionnalités suivantes :
- génère new_datasource.py depuis schema.json
  génère une classe DataSource (parent) + toutes les classes spécialisées dont GenericDataSource, CameraDataSource
- tous les attributs du schema sont disponibles et initialisés à None par défaut
  id est optionnel et généré avec _random_id()
- méthodes: init (avec obligation des attributs required, les autres optionnels), to_dict(), validate(), save(), load(), print() et from_dict() compatibles avec registry.
- documentation automatique dans le docstring de la classe
  documentation de chaque attribut avec type, description et REQUIRED
  R3XA.UNIT documenté comme R3XA.UNIT
- print() affiche tous les attributs, même ceux à None
  les attributs required sont marqués par *
  les R3XA.UNIT sont affichés sous la forme 1392 px
  les listes de R3XA.UNIT deviennent [1392 px, 1040 px]
:::
