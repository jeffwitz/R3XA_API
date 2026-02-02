classdef R3XAFile < handle
    %R3XAFile Minimal MATLAB builder for R3XA JSON files.

    properties
        header
        settings
        data_sources
        data_sets
    end

    methods
        function obj = R3XAFile(varargin)
            if mod(nargin, 2) ~= 0
                error("R3XAFile:NameValue", "Header fields must be name/value pairs.");
            end
            header = struct();
            for i = 1:2:nargin
                header.(varargin{i}) = varargin{i + 1};
            end
            if isfield(header, "version")
                version = header.version;
                header = rmfield(header, "version");
            else
                version = r3xa.schema_version();
            end
            obj.header = header;
            obj.header.version = version;
            obj.settings = {};
            obj.data_sources = {};
            obj.data_sets = {};
        end

        function obj = set_header(obj, varargin)
            if mod(numel(varargin), 2) ~= 0
                error("set_header:NameValue", "Header fields must be name/value pairs.");
            end
            for i = 1:2:numel(varargin)
                obj.header.(varargin{i}) = varargin{i + 1};
            end
        end

        function item = add_setting(obj, kind, varargin)
            item = r3xa.new_item(kind, varargin{:});
            obj.settings{end + 1} = item;
        end

        function item = add_data_source(obj, kind, varargin)
            item = r3xa.new_item(kind, varargin{:});
            obj.data_sources{end + 1} = item;
        end

        function item = add_data_set(obj, kind, varargin)
            item = r3xa.new_item(kind, varargin{:});
            obj.data_sets{end + 1} = item;
        end

        function item = add_generic_setting(obj, title, description, varargin)
            item = obj.add_setting( ...
                "settings/generic", ...
                "title", title, ...
                "description", description, ...
                varargin{:} ...
            );
        end

        function item = add_specimen_setting(obj, title, description, varargin)
            parser = inputParser;
            addParameter(parser, "sizes", []);
            addParameter(parser, "patterning_technique", []);
            parse(parser, varargin{:});
            fields = { ...
                "title", title, ...
                "description", description ...
            };
            if ~isempty(parser.Results.sizes)
                fields = [fields, {"sizes", parser.Results.sizes}];
            end
            if ~isempty(parser.Results.patterning_technique)
                fields = [fields, {"patterning_technique", parser.Results.patterning_technique}];
            end
            extra = parser.Unmatched;
            extra_fields = {};
            extra_names = fieldnames(extra);
            for i = 1:numel(extra_names)
                extra_fields = [extra_fields, {extra_names{i}, extra.(extra_names{i})}];
            end
            item = obj.add_setting("settings/specimen", fields{:}, extra_fields{:});
        end

        function item = add_camera_source( ...
                obj, title, description, output_components, output_dimension, output_units, ...
                manufacturer, model, image_size, varargin)
            fields = { ...
                "title", title, ...
                "description", description, ...
                "output_components", output_components, ...
                "output_dimension", output_dimension, ...
                "output_units", output_units, ...
                "manufacturer", manufacturer, ...
                "model", model, ...
                "image_size", image_size ...
            };
            item = obj.add_data_source("data_sources/camera", fields{:}, varargin{:});
        end

        function item = add_image_set_list( ...
                obj, title, description, path, file_type, data_sources, ...
                time_reference, timestamps, data, varargin)
            fields = { ...
                "title", title, ...
                "description", description, ...
                "path", path, ...
                "file_type", file_type, ...
                "data_sources", data_sources, ...
                "time_reference", time_reference, ...
                "timestamps", timestamps, ...
                "data", data ...
            };
            item = obj.add_data_set("data_sets/list", fields{:}, varargin{:});
        end

        function item = add_image_set_file( ...
                obj, title, description, data_sources, time_reference, timestamps, data, varargin)
            timestamps_payload = r3xa.ensure_data_set_file(timestamps);
            data_payload = r3xa.ensure_data_set_file(data);
            fields = { ...
                "title", title, ...
                "description", description, ...
                "data_sources", data_sources, ...
                "time_reference", time_reference, ...
                "timestamps", timestamps_payload, ...
                "data", data_payload ...
            };
            item = obj.add_data_set("data_sets/file", fields{:}, varargin{:});
        end

        function payload = to_struct(obj)
            payload = obj.header;
            payload.settings = obj.settings;
            payload.data_sources = obj.data_sources;
            payload.data_sets = obj.data_sets;
        end

        function json_text = to_json(obj, varargin)
            pretty = true;
            if nargin > 1
                pretty = varargin{1};
            end
            payload = obj.to_struct();
            if pretty
                try
                    json_text = jsonencode(payload, "PrettyPrint", true);
                    return;
                catch
                end
            end
            json_text = jsonencode(payload);
        end

        function save(obj, filepath, varargin)
            json_text = obj.to_json(varargin{:});
            fid = fopen(filepath, "w");
            if fid == -1
                error("R3XAFile:IO", "Unable to open file for writing: %s", filepath);
            end
            cleanup = onCleanup(@() fclose(fid));
            fwrite(fid, json_text, "char");
        end
    end
end
