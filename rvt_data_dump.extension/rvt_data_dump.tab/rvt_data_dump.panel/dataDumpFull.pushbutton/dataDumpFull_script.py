import clr
clr.AddReference("RevitAPI")
from pyrevit.coreutils import Timer
from rvt_data_dump import data_dump

timer = Timer()

count = data_dump.dump()
for category, amount in count.items():
    print("{} instances of {} exported.".format(amount, category))

print("HdM_pyRevit dataDumpStrColumns run in: ")
print(timer.get_time())
