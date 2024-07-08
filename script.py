#region library
import clr 
import os
import sys
clr.AddReference("System")
import System

clr.AddReference("RevitServices")
import RevitServices
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk
clr.AddReference('PresentationCore')
clr.AddReference('PresentationFramework')
clr.AddReference("System.Windows.Forms")

from Autodesk.Revit.UI import *
from Autodesk.Revit.DB import *
from System.Collections.Generic import *
from Autodesk.Revit.UI.Selection import *
from Autodesk.Revit.DB.Mechanical import *


from System.Windows import MessageBox
from System.IO import FileStream, FileMode, FileAccess
from System.Windows.Markup import XamlReader
#endregion

#region revit infor
# Get the directory path of the script.py & the Window.xaml
dir_path = os.path.dirname(os.path.realpath(__file__))
xaml_file_path = os.path.join(dir_path, "Window.xaml")

#Get UIDocument, Document, UIApplication, Application
uidoc = __revit__.ActiveUIDocument
uiapp = UIApplication(uidoc.Document.Application)
app = uiapp.Application
doc = uidoc.Document
activeView = doc.ActiveView
#endregion

foundation_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFoundation).WhereElementIsElementType().ToElements()
columns_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns).WhereElementIsElementType().ToElements()
wall_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsElementType().ToElements()
beam_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralFraming).WhereElementIsElementType().ToElements()
all_levels = FilteredElementCollector(doc).OfClass(Level).WhereElementIsNotElementType().ToElements()

#region method

class FilterLines(ISelectionFilter):
    def AllowElement(self, element):
        if element.Category.Name == "Lines": return True
        else: return False
             
    def AllowReference(self, reference, position):
        return True


class Utils:
    def get_all_foundation_types(self):
        elements =[]
        for foun_eleype in foundation_collector:
            if isinstance(foun_eleype, WallFoundationType) == False and isinstance(foun_eleype, FloorType) == False:
                name = foun_eleype.FamilyName + ": " + foun_eleype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                elements.append(name)

        elements.sort()
        elements.insert(0,"<None>")
        return elements
    
    def get_all_column_types(self):
        elements =[]
        for ele in columns_collector:
            name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            elements.append(name)
                
        elements.sort()
        elements.insert(0,"<None>")
        return elements
    
    def get_all_wall_types(self):
        elements =[]
        for ele in wall_collector:
            if ele.Kind == WallKind.Basic or ele.Kind == WallKind.Stacked:
                name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                elements.append(name)

        elements.sort()
        elements.insert(0,"<None>")
        return elements
    
    def get_all_beam_types(self):
        elements =[]
        for ele in beam_collector:
            name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            elements.append(name)

        elements.sort()
        elements.insert(0,"<None>")
        return elements
    
    def get_all_levels(self):
        levels = all_levels
        levels = sorted(levels, key=lambda lv: lv.Elevation)
        names = []
        for lv in levels:
            names.append(lv.Name)
        return names

    
    def get_foundation_type_by_name(self, type_name):
        for ele in foundation_collector:
            if isinstance(ele, WallFoundationType) == False and isinstance(ele, FloorType) == False:
                name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                if name == type_name: return ele
        return None
    
    def get_column_type_by_name(self, type_name):
        for ele in columns_collector:
            name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            if name == type_name: return ele
                
        return None
    
    def get_wall_type_by_name(self, type_name):
        for ele in wall_collector:
            name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            if name == type_name: return ele
                
        return None
    
    def get_beam_type_by_name(self, type_name):
        for ele in beam_collector:
            name = ele.FamilyName + ": " + ele.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            if name == type_name: return ele

        return None
    
    def get_level_by_name(self, level_name):
        for lv in all_levels:
            if lv.Name == level_name: return lv

        return None
    
    def find_point_from_start_point(self, line, distance):
        sp = line.GetEndPoint(0)
        ep = line.GetEndPoint(1)
        dir = ep - sp
        tile = distance / dir.GetLength()

        x = tile * dir.X + sp.X
        y = tile * dir.Y + sp.Y
        z = tile * dir.Z + sp.Z

        return XYZ(x, y, z)

    def find_point_from_end_point(self, line, distance):
        sp = line.GetEndPoint(0)
        ep = line.GetEndPoint(1)
        dir =sp - ep
        tile = distance / dir.GetLength()

        x = tile * dir.X + ep.X
        y = tile * dir.Y + ep.Y
        z = tile * dir.Z + ep.Z

        return XYZ(x, y, z)
    
    def get_list_points(self, line, distance, is_start_point):
        number = line.Length / distance
        total = round(number,0)+1
        points = []
        i = 0
        while i < total :
            try:
                if is_start_point:
                    p = self.find_point_from_start_point(line, i*distance)
                else:
                    p = self.find_point_from_end_point(line, i*distance)

                points.append(p)
                i+=1
            except:
                break

        return points


#endregion

#defind window
class WPFWindow:

    def load_window (self, line, pick_point, is_start_point):
        #import window from .xaml file path
        file_stream = FileStream(xaml_file_path, FileMode.Open, FileAccess.Read)
        window = XamlReader.Load(file_stream)

        self.line = line
        self.is_start_point = is_start_point
    
        #controls
        self.bt_Cancel = window.FindName("bt_Cancel")
        self.bt_OK = window.FindName("bt_Ok")
        self.cb_Pile = window.FindName("cb_Pile")
        self.cbb_Pile = window.FindName("cbb_Pile")
        self.cbb_Foundation = window.FindName("cbb_Foundation")
        self.tb_HeightOffset = window.FindName("tb_HeightOffset")
        self.cbb_Ground_Beams = window.FindName("cbb_GroundBeams")
        self.cbb_Top_Beams = window.FindName("cbb_TopBeams")
        self.cbb_Columns = window.FindName("cbb_Columns")
        self.cb_Wall = window.FindName("cb_Wall")
        self.cbb_Wall = window.FindName("cbb_Wall")
        self.tb_Column_Height = window.FindName("tb_ColumnHeight")

        self.cbb_Levels = window.FindName("cbb_Levels")
        self.tb_Distance = window.FindName("tb_Distance")
        self.bindind_data()

        self.window = window
        return window


    def bindind_data (self):
        self.cbb_Pile.ItemsSource = Utils().get_all_foundation_types()
        self.cbb_Pile.SelectedIndex = 1

        self.cbb_Foundation.ItemsSource = Utils().get_all_foundation_types()
        self.cbb_Foundation.SelectedIndex = 1
        self.tb_HeightOffset.Text = "0"

        self.cbb_Columns.ItemsSource = Utils().get_all_column_types()
        self.cbb_Columns.SelectedIndex = 1
        self.tb_Column_Height.Text = "2000"

        self.cbb_Wall.ItemsSource = Utils().get_all_wall_types()
        self.cbb_Wall.SelectedIndex = 1

        self.cbb_Ground_Beams.ItemsSource = Utils().get_all_beam_types()
        self.cbb_Top_Beams.ItemsSource = Utils().get_all_beam_types()
        self.cbb_Ground_Beams.SelectedIndex = 1
        self.cbb_Top_Beams.SelectedIndex = 1

        self.cbb_Levels.ItemsSource = Utils().get_all_levels()
        self.cbb_Levels.SelectedIndex = 0
        self.tb_Distance.Text = "2000"


        self.bt_Cancel.Click += self.cancel_click
        self.bt_OK.Click += self.ok_click
        

    def ok_click(self, sender, e):

        foundation_offset = float(self.tb_HeightOffset.Text)/304.8
        pile_type = Utils().get_foundation_type_by_name(self.cbb_Pile.SelectedValue)
        foundation_type = Utils().get_foundation_type_by_name(self.cbb_Foundation.SelectedValue)
        column_type = Utils().get_column_type_by_name(self.cbb_Columns.SelectedValue)
        ground_beam_type = Utils().get_beam_type_by_name(self.cbb_Ground_Beams.SelectedValue)
        top_beam_type = Utils().get_beam_type_by_name(self.cbb_Top_Beams.SelectedValue)
        wall_type = Utils().get_wall_type_by_name(self.cbb_Wall.SelectedValue)
        level = Utils().get_level_by_name(self.cbb_Levels.SelectedValue)
        distance = float(self.tb_Distance.Text)/304.8
        column_height = float(self.tb_Column_Height.Text)/304.8

        points = Utils().get_list_points(self.line, distance, self.is_start_point)
        start_point = points[0] + XYZ(0,0,level.Elevation)
        end_point = points[len(points)-1] + XYZ(0,0,level.Elevation)
        location_line = Line.CreateBound(start_point, end_point)


        t = Transaction(doc," ")
        t.Start()

        try:
            pile_type.Active()
            foundation_type.Active()
            column_type.Active()
            top_beam_type.Active()
        except:
            pass
        
        column_top_offset = column_height - abs(foundation_offset)
        for p in points:
            pile_offset = 0
            foundation_height = 0
            if foundation_type != None:
                foundation = doc.Create.NewFamilyInstance(p, foundation_type, level, Autodesk.Revit.DB.Structure.StructuralType.Footing)
                foundation.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(foundation_offset)
                doc.Regenerate()

                elevation_at_bottom = foundation.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM).AsDouble()
                elevation_at_top = foundation.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP).AsDouble()
                foundation_height = elevation_at_top - elevation_at_bottom
                pile_offset = foundation_offset - foundation_height

            if pile_type != None:
                pile = doc.Create.NewFamilyInstance(p, pile_type, level, Autodesk.Revit.DB.Structure.StructuralType.Footing)
                pile.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(pile_offset)

            if column_type != None:
                column = doc.Create.NewFamilyInstance(p, column_type, level, Autodesk.Revit.DB.Structure.StructuralType.Column)
                column.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(foundation_offset)
                column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(level.Id)
                column.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(column_top_offset)
        doc.Regenerate()

        if ground_beam_type != None:
            ground_beam = doc.Create.NewFamilyInstance(location_line, ground_beam_type, level, Autodesk.Revit.DB.Structure.StructuralType.Beam)
            doc.Regenerate()
            ground_beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION).Set(foundation_offset)
            ground_beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION).Set(foundation_offset)
        

        top_beam = None
        if top_beam_type != None:
            top_beam = doc.Create.NewFamilyInstance(location_line, top_beam_type, level, Autodesk.Revit.DB.Structure.StructuralType.Beam)
            doc.Regenerate()
            top_beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END0_ELEVATION).Set(column_top_offset)
            top_beam.get_Parameter(BuiltInParameter.STRUCTURAL_BEAM_END1_ELEVATION).Set(column_top_offset)
        
        
        wall_height = column_top_offset
        if top_beam != None:
            beam_elevation_at_top = top_beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_TOP).AsDouble()
            beam_elevation_at_bottom = top_beam.get_Parameter(BuiltInParameter.STRUCTURAL_ELEVATION_AT_BOTTOM).AsDouble()
            beam_height = beam_elevation_at_top - beam_elevation_at_bottom
            wall_height = column_height - beam_height

        if wall_type != None:
            wall = Wall.Create(doc, location_line, level.Id, True)
            wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(foundation_offset)
            wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(-1)
            wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(wall_height)

        t.Commit()

        self.window.Close()

        
    def cancel_click (self, sender, e):
        self.window.Close()
        
#select elements
class Main ():
    def main_task(self):

        line = None
        pick_point = None
        is_start_point = True
        try:
            pick_line = uidoc.Selection.PickObject(Autodesk.Revit.UI.Selection.ObjectType.Element, FilterLines(), "Select Line")
            dLine = doc.GetElement(pick_line)
            line = dLine.GeometryCurve
            sp = line.GetEndPoint(0)
            if isinstance(line, Line):
                pick_point = uidoc.Selection.PickPoint()
                sp_to_pickPoint = round(sp.DistanceTo(pick_point),0)
                if sp_to_pickPoint != 0: is_start_point = False
        except:
            pass
        
        if line != None and pick_point != None:
            window = WPFWindow().load_window(line, pick_point, is_start_point)
            window.ShowDialog()
        
        
if __name__ == "__main__":
    Main().main_task()
                
    
    






