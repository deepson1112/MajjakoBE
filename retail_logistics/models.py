from typing import Iterable
from django.db import models

from user.models import User


from fastkml import kml
from shapely.geometry import shape, Point
from shapely.geometry import mapping

# Create your models here.

class DeliveryDriverLocation(models.Model):
    location_name = models.CharField(max_length=100)
    location_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location_name

class DeliveryDriverStatus(models.Model):
    status =  models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status_code = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driver_status')

    def __str__(self):
        return self.status

class DeliveryDriver(models.Model):
    name = models.CharField(max_length=50)
    primary_phone_number = models.CharField(max_length=12)
    secondary_phone_number = models.CharField(max_length=12)
    location = models.ForeignKey(DeliveryDriverLocation, on_delete=models.CASCADE, related_name='driver')
    status = models.ForeignKey(DeliveryDriverStatus, on_delete=models.CASCADE, related_name='driver')
    vehicle_model = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=50, unique=True)
    license_number = models.CharField(max_length=100, unique=True)
    license_image = models.ImageField(upload_to='license_image/', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.vehicle_model}"

def extract_placemarks(feature):
    placemarks = []
    if hasattr(feature, "geometry"): 
        placemarks.append(feature)
    elif hasattr(feature, "features"):
        for sub_feature in feature.features():
            placemarks.extend(extract_placemarks(sub_feature))
    return placemarks
    
class DeliveryBoundaryKmlFile(models.Model):
    name = models.CharField(max_length=255)
    kml_file = models.FileField(upload_to='kml_files/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        kml_file = self.kml_file

        kml_data = kml_file.read()

        # Parse the KML data
        k = kml.KML()
        k.from_string(kml_data)

        features = list(k.features())
        all_placemarks = []
        for feature in features:
            all_placemarks.extend(extract_placemarks(feature))

        boundary_polygon = shape(all_placemarks[0].geometry)

        # Convert the boundary_polygon to GeoJSON
        boundary_geojson = mapping(boundary_polygon)

        DeliveryBoundary.objects.update_or_create(
            kml_file=self,
            defaults={
                'name': self.name,
                'boundary_geojson': boundary_geojson,
            }
        )
        return super().save(*args, **kwargs)    

    
class DeliveryBoundary(models.Model):
    name = models.CharField(max_length=255)
    boundary_geojson = models.JSONField()
    kml_file = models.ForeignKey(DeliveryBoundaryKmlFile, on_delete=models.CASCADE, related_name="boundary_kml_file")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name