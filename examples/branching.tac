# Branching and loop example in the supported TAC subset
entry:
count = 0
limit = 4
loop:
count = count + 1
if count < limit goto loop
return count
