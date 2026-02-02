function id = random_id(n)
%RANDOM_ID Generate a random lowercase id (default length 24).
if nargin < 1 || isempty(n)
    n = 24;
end
id = char(randi([97 122], 1, n));
end
