#  Copyright 2013 Lars Butler & individual contributors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import json
#-------------------------------------------------------------------------
def load(source_file):
    """
    Converts Esri Json File to GeoJSON.

    :param source_file:
        Path to a file that contains the Esri JSON data.
    
    :returns: 
         A GeoJSON `dict` representing the geometry read from the file.

    """
    with open(source_file, 'r') as reader:
        data = json.loads(reader.read())
        return loads(data)
#-------------------------------------------------------------------------
def loads(string):
    """
    Construct a GeoJSON `dict` from Esri JSON (string/dict).

    :param string:
        The Esri JSON geometry representation

    :returns: 
         A GeoJSON `dict` representing the geometry read from the file.
    """
    if isinstance(string, str):
        string = json.loads(string)
    if 'rings' in string:
        return _esri_to_geojson_convert['rings'](string)
    elif 'paths' in string:
        return _esri_to_geojson_convert['paths'](string)
    elif 'x' in string or 'y' in string:
        return _esri_to_geojson_convert['x'](string)
    elif 'points' in string:
        return _esri_to_geojson_convert['points'](string)
    else:
        raise ValueError(f"Invalid EsriJSON: {string}")
#-------------------------------------------------------------------------
def dump(obj, dest_file):
    """
    Converts GeoJSON to Esri JSON File.
    """
    with open(dest_file, 'w') as writer:
        writer.write(json.dumps(dumps(obj)))
    return dest_file
#-------------------------------------------------------------------------
def dumps(obj):
    """
    Dump a GeoJSON-like `dict` to a Esri JSON.
    """
    if 'type' in obj and \
        obj['type'].lower() in _gj_to_esri.keys():
        convert = _gj_to_esri[obj['type'].lower()]
        return convert(obj)
    else:
        raise ValueError(f"Invalid GeoJSON type {obj}")
#-------------------------------------------------------------------------
def _load_geojson_point(obj):
    """
    Loads GeoJSON to Esri JSON for Geometry type Point.

    """
    coords = obj['coordinates'] 
    return {'x' : coords[0], 'y' : coords[1], "spatialReference" : {'wkid' : 4326}}
#-------------------------------------------------------------------------
def _load_geojson_multipoint(obj):
    """
    Loads GeoJSON to Esri JSON for Geometry type MultiPoint.

    """
    coordkey = ([d for d in obj if d.lower() == 'coordinates']
                     or ['coordinates']).pop()
    return {"points" : obj[coordkey], "spatialReference" : {"wkid" : 4326}}
#-------------------------------------------------------------------------
def _load_geojson_polyline(obj):
    """
    Loads GeoJSON to Esri JSON for Geometry type Linstring and MultiLineString.

    """
    coordkey = ([d for d in obj if d.lower() == 'coordinates']
                or ['coordinates']).pop()
    if obj['type'].lower() == 'linestring':
        coordinates = [obj[coordkey]]
    else:
        coordinates = obj[coordkey]
    return {"paths" : coordinates, "spatialReference" : {"wkid" : 4326}}
#-------------------------------------------------------------------------
def _load_geojson_polygon(data):
    """
    Loads GeoJSON to Esri JSON for Geometry type Polygon or MultiPolygon.

    """
    coordkey = ([d for d in data if d.lower() == 'coordinates']
                     or ['coordinates']).pop()
    coordinates = data[coordkey]
    typekey = ([d for d in data if d.lower() == 'type']
                 or ['type']).pop()
    if data[typekey].lower() == "polygon":
        coordinates = [coordinates]
    part_list = []
    for part in coordinates:
        part_item = []
        for idx, ring in enumerate(part):
            if idx:
                part_item.append(None)
            for coord in ring:
                part_item.append(coord)
        if part_item:
            part_list.append(part_item)
    return {'rings' : part_list, "spatialReference" : {"wkid" : 4326}}
#-------------------------------------------------------------------------
def _dump_esri_point(obj):
    """
    Dump a Esri JSON Point to GeoJSON Point.

    :param dict obj:
        A EsriJSON-like `dict` representing a Point.
    

    :returns:
        GeoJSON representation of the Esri JSON Point
    """
    if obj.get("x", None) is None or \
        obj.get("y", None) is None:
        return {'type': 'Point', 'coordinates': ()}
    return {'type': 'Point', 'coordinates': (obj.get("x"),
                                             obj.get("y"))}
#-------------------------------------------------------------------------
def _dump_esri_polygon(obj):
    """
    Dump a EsriJSON-like Polygon object to GeoJSON.

    Input parameters and return value are the POLYGON equivalent to
    :func:`_dump_point`.
    """
    def split_part(a_part):
        part_list = []
        for item in a_part:
            if item is None:
                if part_list:
                    yield part_list
                part_list = []
            else:
                part_list.append((item[0], item[1]))
        if part_list:
            yield part_list
    part_json = [list(split_part(part))
                    for part in obj['rings']]
    return {'type': 'MultiPolygon', 'coordinates': part_json}
#-------------------------------------------------------------------------
def _dump_esri_multipoint(data):
    """
    Dump a EsriJSON-like MultiPoint object to GeoJSON-dict.

    Input parameters and return value are the MULTIPOINT equivalent to
    :func:`_dump_esri_point`.

    :returns: `dict`
    """

    return {'type': 'Multipoint', 'coordinates': [pt for pt in data['points']]}
#-------------------------------------------------------------------------
def _dump_esri_polyline(data):
    """
    Dump a GeoJSON-like MultiLineString object to WKT.

    Input parameters and return value are the MULTILINESTRING equivalent to
    :func:`_dump_point`.
    """
    return {'type': 'MultiLineString', 'coordinates': [[((pt[0], pt[1]) if pt else None)
                                                        for pt in part]
                                                        for part in data["paths"]]}
#-------------------------------------------------------------------------
_esri_to_geojson_convert = {
    "x" : _dump_esri_point,
    "y" : _dump_esri_point,
    "points" : _dump_esri_multipoint,
    "rings" : _dump_esri_polygon,
    "paths" : _dump_esri_polyline}
#-------------------------------------------------------------------------
_gj_to_esri = {
    "point" : _load_geojson_point,
    "multipoint" : _load_geojson_multipoint,
    "linestring" : _load_geojson_polyline,
    "multilinestring" : _load_geojson_polyline,
    "polygon" : _load_geojson_polygon,
    "multipolygon" : _load_geojson_polygon}