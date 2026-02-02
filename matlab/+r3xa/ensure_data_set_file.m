function payload = ensure_data_set_file(value)
%ENSURE_DATA_SET_FILE Ensure a value is a data_set_file struct.
if isstruct(value)
    payload = value;
    return;
end
if isstring(value) || ischar(value)
    payload = r3xa.data_set_file(value);
    return;
end
error("ensure_data_set_file:Type", "Expected a struct or filename string.");
end
