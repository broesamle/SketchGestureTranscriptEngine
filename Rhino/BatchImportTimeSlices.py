"""Batch import 2D gesture data from PDF files.
Additional information is taken from a CSV protocol file, one CSV per batch.

Jan 2021, by Martin Broesamle.

Based on BatchImport Script by Mitch Heynick, version 30.10.18 - Win or Mac.
Revised 26.11.18 - fixed bug, would not see files with capitalized extensions.
"""

import csv
import sys
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino, os

### Constants
SELECT_FILETYPE = False
PROTOCOL_EXT = '.csv'
PDF_EXT = '.pdf'

def OnMac():
    return Rhino.Runtime.HostUtils.RunningOnOSX

def AddParentToLayerName(layer, parent_layer):
    #adds the parent layer name to the sub layer name to make it unique
    return "{}::{}".format(parent_layer, layer)

class WorkingFileNames(object):
    def __init__(self, folder, ext, alt_ext, protocol_ext=PROTOCOL_EXT):
        #finds all files of chosen filetype in the selected folder
        #returns list of tuples:
        #    (filename, 0) - normal ext. or
        #    (filename, 1) - alt. ext.
        #returns empty list if no matching filenames found
        self.filenames = []
        self.protocol = None
        for filename in os.listdir(folder):
            if filename.lower().endswith(ext):
                self.filenames.append((filename[:-len(ext)], 0))
            elif alt_ext and filename.lower().endswith(alt_ext):
                self.filenames.append((filename[:-len(alt_ext)], 1))
            elif filename.lower().endswith(protocol_ext):
                if self.protocol is not None:
                    msg = "Ignoring additional protocol file %s" % filename
                    rs.MessageBox(msg, 0, "Warning")
                else:
                    self.protocol = filename
        self.filenames.sort()

def AddNumberSuffix(name, copy_count):
    return "{}_Copy_{}".format(name, copy_count)

def ProcessFolder(folder, ext, alt_ext, copy_count):
    wfnames = WorkingFileNames(folder, ext, alt_ext)
    if not wfnames.protocol:
        msg = "No protocol file."
        raise ValueError(msg)
    else:
        csvfile = open(os.path.join(folder, wfnames.protocol), 'rb')
        csvreader = csv.reader(csvfile, dialect = 'excel-tab')
        protocol = []
        for row in csvreader:
            protocol.append(row)
    if len(protocol) != len(wfnames.filenames):
        msg = ("Number of protocol entries %d does not match number of PDF files %d."
               % (len(protocol), len(wfnames.filenames)))
        raise ValueError(msg)
    if not wfnames.filenames: return
    obj_count = 0
    file_count = 0
    raise_copy_count = False
    rs.AddLayer("id-labels")
    for filename, protorow in zip(wfnames.filenames, protocol):
        while len(protorow) < 4:
            protorow.append("")
        stroke_id, target_layer, fingercodes, timestamp  = protorow
        print("Importing %s; ID:%s LAY:%s FNG:%s"
              % (filename, stroke_id, target_layer, fingercodes))
        if not filename[1]:
            #normal extension
            fullpath = os.path.join(folder, filename[0]+ext).lower()
        else:
            #alt extension
            fullpath = os.path.join(folder, filename[0]+alt_ext).lower()
        #get existing layer set
        exist_layers = set(rs.LayerNames())
        #import file
        rs.Command('_-Import "{}" _Enter'.format(fullpath), False)
        if rs.LastCommandResult()==0: file_count+=1
        lco = rs.LastCreatedObjects(False)
        if lco: obj_count+=len(lco)
        #move imported objects: timestamp becomes z position
        if len(lco) > 0:
            rs.MoveObjects(lco, (0, 0, 2*file_count))
        if not rs.IsLayer(target_layer):
            p_layer = rs.AddLayer(target_layer)
        rs.ObjectLayer(lco, target_layer)
        txtobj = rs.AddText("imported: " + stroke_id, (0, 20, 2*file_count))
        rs.ObjectLayer(txtobj, "id-labels")
    return True, file_count, obj_count, raise_copy_count

def BatchImportWithSublayers():
    #UI
    fTypes = ["Rhino", "STL", "DXF", "DWG", "PDF", "IGES", "STEP", "SolidWorks"]
    if "BI_PrevFolder" in sc.sticky: prevFolder = sc.sticky["BI_PrevFolder"]
    else: prevFolder = rs.WorkingFolder()
    if "BI_PrevFileType" in sc.sticky: prevFileType = sc.sticky["BI_PrevFileType"]
    else: prevFileType = fTypes[0]
    #copy count data stored in document (string data!!)
    if rs.IsDocumentData():
        copy_count = rs.GetDocumentData("BI_CopyCount", "Current_Count")
    else:
        copy_count = 0
    if not copy_count:
        rs.SetDocumentData("BI_CopyCount", "Current_Count", "0")
    copy_count = rs.GetDocumentData("BI_CopyCount", "Current_Count")
    msg = "Select folder to process"
    title = "Batch Import"
    folder = rs.BrowseForFolder(message=msg)
    if not folder : return
    if SELECT_FILETYPE:
        msg = "Select file type to import"
        fType = rs.ListBox(fTypes, msg, title, prevFileType)
        if not fType: return
        alt_ext = None
        if fType==fTypes[0]:
            ext = ".3dm"
        elif fType==fTypes[6]:
            ext = ".stp" ; alt_ext = ".step"
        elif fType==fTypes[7]:
            ext = ".sldprt"
        elif fType==fTypes[5]:
            ext = ".igs" ; alt_ext = ".iges"
        else:
            ext = "."+fType.lower()
    else:
        ext = PDF_EXT
        alt_ext = None
    #Process the folder
    total_count = 0
    rs.EnableRedraw(False)
    rc, file_count, obj_count, raise_cc = ProcessFolder(folder,
                                                        ext,
                                                        alt_ext,
                                                        copy_count)
    rs.Redraw()
    if not rc:
        msg = "No files of chosen type found in folder!"
    else:
        msg = "{} files with {} total objects imported".format(
                    file_count, obj_count)
    rs.MessageBox(msg, 0, "File Import")
    rs.UnselectAllObjects()
    if raise_cc:
        copy_count = str(int(copy_count)+1)
        rs.SetDocumentData("BI_CopyCount", "Current_Count", copy_count)
    #store last used file type, folder
    sc.sticky["BI_PrevFolder"] = folder
    if SELECT_FILETYPE:
        sc.sticky["BI_PrevFileType"] = fType

BatchImportWithSublayers()
