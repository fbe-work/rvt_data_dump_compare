import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import BuiltInCategory as Bic
from pyrevit.coreutils import Timer
from rvt_data_dump import data_dump

timer = Timer()

count = data_dump.dump(
    typed_categories=[Bic.OST_StructuralColumns],
)

for category, amount in count.items():
    print("{} instances of {} exported.".format(amount, category))
print("HdM_pyRevit dataDumpStrColumns run in: ")

print(timer.get_time())
