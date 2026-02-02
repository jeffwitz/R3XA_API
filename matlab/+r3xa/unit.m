function payload = unit(title, value, unit_name, scale, varargin)
%UNIT Create a R3XA unit payload.
if nargin < 4 || isempty(scale)
    scale = 1.0;
end
if mod(numel(varargin), 2) ~= 0
    error("unit:NameValue", "Extra fields must be name/value pairs.");
end
payload = struct( ...
    "kind", "unit", ...
    "title", title, ...
    "value", value, ...
    "unit", unit_name, ...
    "scale", scale ...
);
for i = 1:2:numel(varargin)
    field = varargin{i};
    value = varargin{i + 1};
    payload.(field) = value;
end
end
