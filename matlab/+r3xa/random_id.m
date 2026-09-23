function id = random_id(kind, n)
%RANDOM_ID Generate a canonical, non-reproducible R3XA identifier.
if nargin < 1 || isempty(kind)
    kind = '';
end
if nargin < 2 || isempty(n)
    if isnumeric(kind)
        n = kind;
        kind = '';
    else
        n = 12;
    end
elseif isnumeric(kind)
    error("random_id:Arguments", "The kind must be text when a length is supplied.");
end

prefix = 'r3xa-';
parts = strsplit(char(kind), '/');
if numel(parts) == 2
    section_prefix = { ...
        'settings', 'stg'; ...
        'data_sources', 'src'; ...
        'data_sets', 'set' ...
    };
    section_index = find(strcmp(section_prefix(:, 1), parts{1}), 1);
    if ~isempty(section_index) && ~isempty(parts{2})
        prefix = [section_prefix{section_index, 2}, '-', parts{2}, '-'];
    end
end

uuid = lower(strrep(char(java.util.UUID.randomUUID()), '-', ''));
if n > numel(uuid)
    error("random_id:Length", "The identifier suffix cannot exceed %d characters.", numel(uuid));
end
id = [prefix, uuid(1:n)];
end
