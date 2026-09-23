%TEST_SMOKE Exercise the supported MATLAB binding without a server.
matlab_root = fileparts(mfilename("fullpath"));
addpath(matlab_root);

setting = r3xa.new_item("settings/specimen", "title", "Specimen");
source = r3xa.new_item("data_sources/camera", "title", "Camera");
dataset = r3xa.new_item("data_sets/list", "title", "Images");

assert(startsWith(setting.id, 'stg-specimen-'));
assert(startsWith(source.id, 'src-camera-'));
assert(startsWith(dataset.id, 'set-list-'));
assert(~strcmp(setting.id, r3xa.new_item("settings/specimen").id));
assert(numel(setting.id) == numel('stg-specimen-') + 12);
assert(numel(source.id) == numel('src-camera-') + 12);
assert(numel(dataset.id) == numel('set-list-') + 12);

output_path = string([tempname, '.json']);
cleanup = onCleanup(@() delete_if_present(output_path));
document = r3xa.R3XAFile( ...
    "title", "Essai UTF-8", ...
    "description", "Métadonnées expérimentales", ...
    "date", "2026-09-23" ...
);
document.save(output_path);
json_text = fileread(output_path);
assert(contains(json_text, "Métadonnées expérimentales"));

disp("MATLAB binding smoke test passed");

function delete_if_present(filepath)
if isfile(filepath)
    delete(filepath);
end
end
