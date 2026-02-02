function payload = data_set_file(filename, delimiter, data_range, varargin)
%DATA_SET_FILE Create a data_set_file payload.
if nargin < 2
    delimiter = [];
end
if nargin < 3
    data_range = [];
end
if mod(numel(varargin), 2) ~= 0
    error("data_set_file:NameValue", "Extra fields must be name/value pairs.");
end
payload = struct( ...
    "kind", "data_set_file", ...
    "filename", filename ...
);
if ~isempty(delimiter)
    payload.delimiter = delimiter;
end
if ~isempty(data_range)
    payload.data_range = data_range;
end
for i = 1:2:numel(varargin)
    field = varargin{i};
    value = varargin{i + 1};
    payload.(field) = value;
end
end
