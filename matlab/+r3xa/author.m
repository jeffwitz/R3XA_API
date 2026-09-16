function payload = author(name, affiliation, orcid, varargin)
%AUTHOR Create a R3XA author payload.
%   Since schema 2026.9.16 an author is an object carrying its own ORCID,
%   instead of a bare name paired with a parallel author_orcids array.
if nargin < 1 || strlength(string(name)) == 0
    error("author:Name", "author requires a non-empty name.");
end
if mod(numel(varargin), 2) ~= 0
    error("author:NameValue", "Extra fields must be name/value pairs.");
end
payload = struct("name", name);
if nargin >= 2 && ~isempty(affiliation)
    payload.affiliation = affiliation;
end
if nargin >= 3 && ~isempty(orcid)
    payload.orcid = orcid;
end
for i = 1:2:numel(varargin)
    field = varargin{i};
    value = varargin{i + 1};
    payload.(field) = value;
end
end
