function item = new_item(kind, varargin)
%NEW_ITEM Create a new R3XA item with id/kind and extra fields.
if mod(numel(varargin), 2) ~= 0
    error("new_item:NameValue", "Extra fields must be name/value pairs.");
end
item = struct();
for i = 1:2:numel(varargin)
    field = varargin{i};
    value = varargin{i + 1};
    item.(field) = value;
end
if ~isfield(item, "id")
    item.id = r3xa.random_id();
end
item.kind = kind;
end
