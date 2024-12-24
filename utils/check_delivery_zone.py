from shapely.geometry import shape, Point
from retail_logistics.models import DeliveryBoundary

def check_delivery_zone(lat, lon):
    boundary_record = DeliveryBoundary.objects.first()
    boundary_polygon = shape(boundary_record.boundary_geojson)

    customer_location = Point(lon, lat)
    if boundary_polygon.contains(customer_location):
        return True
    else:
        return False