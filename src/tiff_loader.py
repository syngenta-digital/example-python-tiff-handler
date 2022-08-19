import affine as affine
import rasterio
from rasterio.mask import mask
import shapely.geometry
import shapely.ops
import cv2
import numpy as np
import pyproj
import geopandas as gpd
from typing import Dict
import argparse


class TiffLoader:

    def __init__(self, image_filename: str, shape_filename: str) -> None:
        """
        Init the class.
        :param image_filename: (str) location and name of the image file
        :param shape_filename: (str) location and name of the shapefile
        """
        shape = None
        if shape_filename is not None:
            image_crs = rasterio.open(image_filename).crs
            shape = self.load_shape(shape_filename, image_crs)

        self.tif_image, self.tif_transform, self.tif_meta = self.load_tif_image(image_filename, shape)
        self.png_image = self.create_png_image()

    # -- SAVE/CREATE Methods
    def create_png_image(self) -> np.ndarray:
        """
        Creates a numpy array to represent the image data.
        :return:
        png_image: (np.ndarray) array representing the PNG data
        """
        tmp = np.nan_to_num(self.tif_image)
        tmp = tmp.astype(int)

        if self.tif_image.shape[0] == 1:
            png_image = np.zeros((self.tif_image.shape[1], self.tif_image.shape[2], 1), np.uint8)
            png_image[:, :, 0] = tmp[0, :, :]
        else:
            png_image = np.zeros((self.tif_image.shape[1], self.tif_image.shape[2], 3), np.uint8)
            png_image[:, :, 2] = tmp[0, :, :]
            png_image[:, :, 1] = tmp[1, :, :]
            png_image[:, :, 0] = tmp[2, :, :]

        return png_image

    def save_tif_image(self, output_filename: str) -> None:
        """
        Saves the numpy array as a TIFF image.
        :param output_filename: (str) location and name of the output file
        :return: None
        """
        self.tif_meta.update({"driver": "GTiff",
                              "height": self.tif_image.shape[1],
                              "width": self.tif_image.shape[2],
                              "transform": self.tif_transform})

        with rasterio.open(output_filename, "w", **self.tif_meta) as dest:
            dest.write(self.tif_image)

    def save_png_image(self, output_filename: str) -> None:
        """
        Saves the numpy array as a PNG image.
        :param output_filename: (str) location and name of the output file
        :return: None
        """
        cv2.imwrite(output_filename, self.png_image)

    # -- GET methods
    def get_tif_image(self) -> np.ndarray:
        """
        Returns the numpy array representing the TIFF image.
        Returns
        :return:
        tif_image: (np.ndarray) numpy array representing the TIFF image
        """
        return self.tif_image

    def get_png_image(self) -> np.ndarray:
        """
        Returns the numpy array representing the PNG image.
        :return:
        png_image: (np.ndarray) numpy array representing the PNG image
        """
        return self.png_image

    @staticmethod
    def load_tif_image(image_filename: str, shape: shapely.geometry.multipolygon.MultiPolygon) -> \
            (np.ndarray, affine.Affine, Dict):
        """
        Loads the TIFF image and mask it with shapefile.
        :param image_filename: (str) location and name of the TIFF image
        :param shape: (shapely.geometry.multipolygon.MultiPolygon) shapefile related to the area
        :return:
        tif_image (np.ndarray) numpy array representing the TIFF image
        tif_transform: (affine.Affine) affine transformation used to raster the image
        tif_meta: (Dict) dictionary with more meta information
        """
        tif_transform = None
        with rasterio.open(image_filename) as src:
            if shape is not None:
                tif_image, tif_transform = mask(src, [shape], crop=True)
            else:
                tif_image = src.read()
            tif_meta = src.meta
        return tif_image, tif_transform, tif_meta

    @staticmethod
    def load_shape(shape_filename: str, image_crs: rasterio.crs.CRS) -> \
            shapely.geometry.multipolygon.MultiPolygon:
        """
        Loads the shapefile.
        :param shape_filename: (str) location and name of shapefile
        :param image_crs: (rasterio.crs.CRS) coordinate reference system associated to the image
        :return:
        unified_shapes: (shapely.geometry.multipolygon.MultiPolygon) multipolygon in shapely format
        """
        shapes = gpd.read_file(shape_filename)['geometry']
        shapes = shapes.to_crs(image_crs)

        shapely_shapes = list()
        for i in range(0, len(shapes)):
            if shapely.geometry.shape(shapes[i]).is_valid:
                shapely_shapes.append(shapely.geometry.shape(shapes[i]))

        unified_shape = shapely_shapes[0]
        for i in range(0, len(shapely_shapes)):
            unified_shape = unified_shape.union(shapely_shapes[i])

        return unified_shape

    @staticmethod
    def check_projections(image_filename: str, shape_filename: str) -> (pyproj.crs.crs.CRS, rasterio.crs.CRS):
        """
        Checks the coordinate reference systems
        :param image_filename: (str) location and name of the TIFF image
        :param shape_filename:  (str) location and name of the shapefile
        :return:
        geo_shape.crs: (pyproj.crs.crs.CRS) coordinate reference system associated to the image
        imagery.crs: (rasterio.crs.CRS) coordinate reference system associated to the image
        """
        imagery = rasterio.open(image_filename)
        geo_shapes = gpd.read_file(shape_filename)
        return geo_shapes.crs, imagery.crs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()

    ap.add_argument("-i", "--input_image", required=True, help="input image")
    ap.add_argument("-s", "--input_shapefile", required=False, default=None, type=str,
                    help="input shapefile")
    ap.add_argument("-o", "--output_image", required=True, help="output image")
    args = ap.parse_args()
    input_image = args.input_image
    input_shapefile = args.input_shapefile
    output_image = args.output_image

    loader = TiffLoader(input_image, input_shapefile)
    loader.save_png_image(output_image)
